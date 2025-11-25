"""Core synchronization logic for pixi-sync-environment."""

import logging
from pathlib import Path
from typing import Any, Callable

from pixi_sync_environment.io import (
    get_manifest_path,
    load_environment_file,
    save_environment_file,
)
from pixi_sync_environment.pixi_environment import (
    PixiError,
    export_conda_environment,
)

logger = logging.getLogger(__name__)


def pixi_sync_environment(
    path_dir: Path,
    environment: str = "default",
    environment_file: str = "environment.yml",
    name: str | None = None,
    check: bool = False,
    show_diff_callback: Callable[
        [dict[str, Any] | list[Any] | None, dict[str, Any], str], None
    ]
    | None = None,
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
    name : str or None, optional
        Environment name to set in the conda environment file.
        If None, pixi uses the environment name. Default is None.
    check : bool, optional
        If True, only check if files are in sync without modifying them.
        Default is False.
    show_diff_callback : callable or None, optional
        Callback function to show differences when files are out of sync.
        Called with (current_dict, new_dict, environment_file).
        If None, no diff is shown. Default is None.

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
    """
    try:
        current_environment_dict = load_environment_file(
            path_dir, environment_file, raise_exception=False
        )

        manifest_path = get_manifest_path(path_dir)

        new_environment_dict = export_conda_environment(
            manifest_path,
            environment=environment,
            name=name,
        )

        if not current_environment_dict:
            if check:
                logger.warning(
                    "Environment file %s does not exist",
                    path_dir / environment_file,
                )
                if show_diff_callback:
                    show_diff_callback(
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
                if show_diff_callback:
                    show_diff_callback(
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
