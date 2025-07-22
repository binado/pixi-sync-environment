import logging
import sys
from pathlib import Path
from pprint import pprint

from pre_commit_pixi_environment_file.io import (
    find_project_dir,
    load_environment_file,
    save_environment_file,
)
from pre_commit_pixi_environment_file.parser import get_parser
from pre_commit_pixi_environment_file.pixi_environment import (
    create_environment_dict_from_pixi,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def sync_environments(
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
    new_environment_dict = create_environment_dict_from_pixi(
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
    path_dir = find_project_dir(root_dir=args.root_dir)
    if path_dir is None:
        sys.exit(1)

    sync_environments(
        path_dir,
        environment_file=args.environment_file,
        explicit=args.explicit,
        name=args.name,
        prefix=args.prefix,
        include_pip_packages=args.include_pip_packages,
        include_conda_channels=args.include_conda_channels,
        include_build=args.include_build,
    )
