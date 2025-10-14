"""Command-line interface for pixi-sync-environment.

This module provides the CLI functionality for synchronizing pixi environments
with conda environment.yml files.
"""

import argparse
import difflib
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from pixi_sync_environment import pixi_sync_environment
from pixi_sync_environment.io import CONFIG_FILENAMES, find_project_dir
from pixi_sync_environment.pixi_environment import PixiError

logger = logging.getLogger(__name__)


def _show_diff(
    current_dict: dict[str, Any] | list[Any] | None,
    new_dict: dict[str, Any],
    environment_file: str,
) -> None:
    """Show the difference between current and new environment files.

    Parameters
    ----------
    current_dict : dict or list or None
        Current environment dictionary, or None if file doesn't exist.
    new_dict : dict
        New environment dictionary generated from pixi.
    environment_file : str
        Name of the environment file for display purposes.
    """
    if current_dict is None:
        logger.info("Diff: %s does not exist and would be created", environment_file)
        # Show what would be created
        new_yaml = yaml.dump(
            new_dict, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        print("\nNew file content:")
        print("---")
        print(new_yaml)
        print("---")
    else:
        # Convert both to YAML strings for comparison
        current_yaml = yaml.dump(
            current_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        ).splitlines(keepends=True)
        new_yaml = yaml.dump(
            new_dict, default_flow_style=False, allow_unicode=True, sort_keys=False
        ).splitlines(keepends=True)

        # Generate unified diff
        diff = difflib.unified_diff(
            current_yaml,
            new_yaml,
            fromfile=f"current {environment_file}",
            tofile=f"new {environment_file}",
            lineterm="",
        )

        diff_lines = list(diff)
        if diff_lines:
            print(f"\nDifferences in {environment_file}:")
            print("".join(diff_lines))


def get_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Sets up all command-line arguments and options for the pixi-sync-environment
    tool, including file inputs, environment configuration, and output options.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser ready to parse command-line arguments.

    Examples
    --------
    >>> parser = get_parser()
    >>> args = parser.parse_args(['pixi.toml', '--name', 'myenv'])
    >>> args.name
    'myenv'
    """
    parser = argparse.ArgumentParser(
        description="Compare and update conda environment files using pixi manifest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input_files",
        nargs="+",
        type=Path,
        help=f"Path to configuration files ({'/'.join(CONFIG_FILENAMES)})",
    )

    parser.add_argument(
        "--environment-file",
        type=str,
        default="environment.yml",
        help="Name of the environment file",
    )

    parser.add_argument(
        "--explicit",
        action="store_true",
        default=False,
        help="Use explicit package specifications",
    )

    parser.add_argument(
        "--name", type=str, default=None, help="Environment name (optional)"
    )

    parser.add_argument(
        "--prefix", type=str, default=None, help="Environment prefix path (optional)"
    )

    parser.add_argument(
        "--environment", type=str, default="default", help="Name of pixi environment"
    )

    parser.add_argument(
        "--include-pip-packages",
        action="store_true",
        default=False,
        help="Include pip packages in the environment",
    )

    parser.add_argument(
        "--no-include-conda-channels",
        action="store_false",
        dest="include_conda_channels",
        default=True,
        help="Exclude conda channels from the environment",
    )

    parser.add_argument(
        "--include-build",
        action="store_true",
        default=False,
        help="Include build information",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Check if files are in sync without modifying them (exits with code 1 if out of sync)",
    )

    return parser


def main() -> None:
    """Main entry point for the command-line interface.

    Parses command-line arguments, validates input files, and processes
    each project directory to synchronize pixi environments with conda
    environment files.

    This function handles multiple project directories and provides
    appropriate error handling and logging for the CLI experience.

    Raises
    ------
    SystemExit
        If no valid project directories are found or if critical errors occur.

    Examples
    --------
    Command-line usage:
        $ pixi_sync_environment pixi.toml
        $ pixi_sync_environment --name myenv --include-pip-packages pixi.toml
        $ pixi_sync_environment --environment dev pyproject.toml
        $ pixi_sync_environment --check pixi.toml

    Notes
    -----
    - Supports processing multiple project directories in a single run
    - Continues processing remaining directories even if one fails
    - Uses logging for user feedback instead of print statements
    - Exit code 1 indicates failure, 0 indicates success
    """
    try:
        args = get_parser().parse_args()

        # Find and validate project directories
        try:
            project_dirs = find_project_dir(args.input_files)
        except ValueError as err:
            logger.error("Invalid input files: %s", err)
            sys.exit(1)

        if not project_dirs:
            logger.error("No valid project directories found")
            sys.exit(1)

        # Process each project directory
        success_count = 0
        in_sync_count = 0
        total_count = len(project_dirs)

        for project_dir in project_dirs:
            try:
                if args.check:
                    logger.info("Checking sync status for directory %s", project_dir)
                else:
                    logger.info("Syncing environment for directory %s", project_dir)

                is_in_sync = pixi_sync_environment(
                    project_dir,
                    environment=args.environment,
                    environment_file=args.environment_file,
                    explicit=args.explicit,
                    name=args.name,
                    prefix=args.prefix,
                    include_pip_packages=args.include_pip_packages,
                    include_conda_channels=args.include_conda_channels,
                    include_build=args.include_build,
                    check=args.check,
                    show_diff_callback=_show_diff if args.check else None,
                )
                success_count += 1
                if is_in_sync:
                    in_sync_count += 1

            except PixiError as err:
                logger.error("Failed to sync environment in %s: %s", project_dir, err)
                if err.stderr:
                    logger.debug("pixi stderr: %s", err.stderr)

            except (ValueError, FileNotFoundError) as err:
                logger.error("Configuration error in %s: %s", project_dir, err)

            except Exception as err:
                logger.error("Unexpected error in %s: %s", project_dir, err)
                logger.debug("Full traceback:", exc_info=True)

        # Report final status
        if args.check:
            # In check mode, report sync status
            if in_sync_count == total_count:
                logger.info("All %d directories are in sync", total_count)
            elif in_sync_count > 0:
                logger.warning(
                    "Partially in sync: %d/%d directories",
                    in_sync_count,
                    total_count,
                )
                sys.exit(1)
            else:
                logger.error("No directories in sync (%d checked)", total_count)
                sys.exit(1)
        else:
            # In sync mode, report success/failure
            if success_count == total_count:
                logger.info(
                    "Successfully synced %d/%d directories", success_count, total_count
                )
            elif success_count > 0:
                logger.warning(
                    "Partially successful: synced %d/%d directories",
                    success_count,
                    total_count,
                )
                sys.exit(1)
            else:
                logger.error(
                    "Failed to sync any directories (%d attempted)", total_count
                )
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as err:
        logger.error("Unexpected error: %s", err)
        logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)
