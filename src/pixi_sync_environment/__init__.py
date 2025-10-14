"""Pixi-sync-environment: Sync pixi environments with conda environment.yml files.

This package provides functionality to synchronize pixi project environments
with traditional conda environment.yml files, making it easier to maintain
compatibility between pixi and conda workflows.

Main Functions
--------------
main : function
    Command-line entry point for the synchronization tool.
pixi_sync_environment : function
    Core synchronization function that can be used programmatically.
get_parser : function
    Creates the argument parser for command-line interface.

Examples
--------
Using from command line:
    $ pixi_sync_environment pixi.toml
    $ pixi_sync_environment --environment-file env.yml --name myenv pixi.toml

Using programmatically:
    >>> from pixi_sync_environment import pixi_sync_environment
    >>> from pathlib import Path
    >>> pixi_sync_environment(Path("/project"), environment="default")
"""

import argparse
import difflib
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from pixi_sync_environment.io import (
    CONFIG_FILENAMES,
    find_project_dir,
    get_manifest_path,
    load_environment_file,
    save_environment_file,
)
from pixi_sync_environment.pixi_environment import (
    PixiError,
    create_environment_dict_from_pixi,
)

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


def pixi_sync_environment(
    path_dir: Path,
    environment: str = "default",
    environment_file: str = "environment.yml",
    explicit: bool = False,
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
    check: bool = False,
) -> bool:
    """Synchronize a pixi environment with a conda environment file.

    Compares the current conda environment file with the pixi environment
    specification and updates the conda file if they differ. If no environment
    file exists, creates a new one.

    Parameters
    ----------
    path_dir : Path
        Directory containing the pixi project and environment file.
    environment : str, optional
        Name of the pixi environment to sync. Default is "default".
    environment_file : str, optional
        Name of the conda environment file to create/update.
        Default is "environment.yml".
    explicit : bool, optional
        Whether to include only explicitly requested packages (not dependencies).
        Default is False.
    name : str or None, optional
        Environment name to set in the conda environment file.
        If None, no name is set. Default is None.
    prefix : str or None, optional
        Environment prefix path to set in the conda environment file.
        If None, no prefix is set. Default is None.
    include_pip_packages : bool, optional
        Whether to include PyPI packages in the environment file.
        Default is False.
    include_conda_channels : bool, optional
        Whether to include conda channels in the environment file.
        Default is True.
    include_build : bool, optional
        Whether to include build strings in package specifications.
        Default is False.
    check : bool, optional
        If True, only check if files are in sync without modifying them.
        Default is False.

    Returns
    -------
    bool
        True if files are in sync, False if they differ.

    Raises
    ------
    PixiError
        If pixi command fails or is not available.
    ValueError
        If no pixi manifest is found in the directory.
    FileNotFoundError
        If the specified pixi manifest doesn't exist.

    Examples
    --------
    >>> from pathlib import Path
    >>> pixi_sync_environment(Path("/project"))  # doctest: +SKIP

    >>> # Sync with specific environment and options
    >>> pixi_sync_environment(  # doctest: +SKIP
    ...     Path("/project"),
    ...     environment="dev",
    ...     name="myproject-dev",
    ...     include_pip_packages=True
    ... )

    Notes
    -----
    - If the environment file doesn't exist, it will be created
    - If the environment file exists but differs from pixi, it will be updated
    - If the files are already in sync, no changes are made
    - All file operations preserve UTF-8 encoding and proper YAML formatting
    """
    try:
        # Load existing environment file if it exists
        current_environment_dict = load_environment_file(
            path_dir, environment_file, raise_exception=False
        )

        # Find and validate pixi manifest
        manifest_path = get_manifest_path(path_dir)

        # Generate new environment dictionary from pixi
        new_environment_dict = create_environment_dict_from_pixi(
            manifest_path,
            environment,
            explicit=explicit,
            name=name,
            prefix=prefix,
            include_pip_packages=include_pip_packages,
            include_conda_channels=include_conda_channels,
            include_build=include_build,
        )

        # Compare and update if necessary
        if not current_environment_dict:
            if check:
                logger.warning(
                    "Environment file %s does not exist",
                    path_dir / environment_file,
                )
                _show_diff(
                    current_environment_dict, new_environment_dict, environment_file
                )
                return False
            else:
                logger.info(
                    "Environment file not found, creating new %s",
                    path_dir / environment_file,
                )
                save_environment_file(
                    new_environment_dict, path_dir, environment_file=environment_file
                )
                return True
        elif current_environment_dict != new_environment_dict:
            if check:
                logger.warning(
                    "Environment file %s is out of sync with pixi manifest",
                    environment_file,
                )
                _show_diff(
                    current_environment_dict, new_environment_dict, environment_file
                )
                return False
            else:
                logger.info(
                    "Environment file %s is out of sync, updating", environment_file
                )
                save_environment_file(
                    new_environment_dict, path_dir, environment_file=environment_file
                )
                return True
        else:
            logger.info("Environment file %s is already in sync", environment_file)
            return True

    except PixiError as err:
        logger.error("Pixi operation failed: %s", err)
        raise
    except ValueError as err:
        logger.error("Configuration error: %s", err)
        raise
    except Exception as err:
        logger.error("Unexpected error during sync: %s", err)
        raise


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
