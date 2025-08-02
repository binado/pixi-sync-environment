import argparse
import logging
import sys
from pathlib import Path

from pixi_sync_environment.io import (
    CONFIG_FILENAMES,
    find_project_dir,
    get_manifest_path,
    load_environment_file,
    save_environment_file,
)
from pixi_sync_environment.pixi_environment import (
    create_environment_dict_from_pixi,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    """Create an ArgumentParser for the compare_environments function."""
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
        "--include-pip-packages",
        action="store_true",
        default=False,
        help="Include pip packages in the environment",
    )

    parser.add_argument(
        "--include-conda-channels",
        action="store_true",
        dest="include_conda_channels",
        default=True,
        help="Include conda channels from the environment",
    )

    parser.add_argument(
        "--include-build",
        action="store_true",
        default=False,
        help="Include build information",
    )

    return parser


def pixi_sync_environment(
    path_dir: Path,
    environment_file: str = "environment.yml",
    explicit: bool = False,
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
):
    current_environment_dict = load_environment_file(
        path_dir, environment_file, raise_exception=False
    )
    manifest_path = get_manifest_path(path_dir)
    new_environment_dict = create_environment_dict_from_pixi(
        manifest_path,
        explicit=explicit,
        name=name,
        prefix=prefix,
        include_pip_packages=include_pip_packages,
        include_conda_channels=include_conda_channels,
        include_build=include_build,
    )
    if not current_environment_dict:
        logger.info(
            "Couldn't load environment file, writing to %s", path_dir / environment_file
        )
        save_environment_file(
            new_environment_dict, path_dir, environment_file=environment_file
        )
    elif current_environment_dict != new_environment_dict:
        logger.info("%s not in sync with environment", environment_file)
        save_environment_file(
            new_environment_dict, path_dir, environment_file=environment_file
        )
    else:
        logger.info("environment.yml file already in sync")


def main() -> None:
    args = get_parser().parse_args()
    project_dirs = find_project_dir(args.input_files)
    if not project_dirs:
        sys.exit(1)

    for dir in project_dirs:
        logger.info("Syncing environment for directory %s", dir)
        pixi_sync_environment(
            dir,
            environment_file=args.environment_file,
            explicit=args.explicit,
            name=args.name,
            prefix=args.prefix,
            include_pip_packages=args.include_pip_packages,
            include_conda_channels=args.include_conda_channels,
            include_build=args.include_build,
        )
