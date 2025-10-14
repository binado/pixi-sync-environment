"""Pixi-sync-environment: Sync pixi environments with conda environment.yml files.

This package provides functionality to synchronize pixi project environments
with traditional conda environment.yml files, making it easier to maintain
compatibility between pixi and conda workflows.

Main Functions
--------------
pixi_sync_environment : function
    Core synchronization function that can be used programmatically.

Examples
--------
Using programmatically:
    >>> from pixi_sync_environment import pixi_sync_environment
    >>> from pathlib import Path
    >>> pixi_sync_environment(Path("/project"), environment="default")

Using from command line:
    $ pixi_sync_environment pixi.toml
    $ pixi_sync_environment --environment-file env.yml --name myenv pixi.toml
    $ pixi_sync_environment --check pixi.toml
"""

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
    create_environment_dict_from_pixi,
)

logger = logging.getLogger(__name__)

__all__ = ["pixi_sync_environment", "PixiError"]


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

    >>> # Check mode without modifying files
    >>> is_synced = pixi_sync_environment(  # doctest: +SKIP
    ...     Path("/project"),
    ...     check=True
    ... )

    Notes
    -----
    - If the environment file doesn't exist, it will be created
    - If the environment file exists but differs from pixi, it will be updated
    - If the files are already in sync, no changes are made
    - All file operations preserve UTF-8 encoding and proper YAML formatting
    - In check mode, files are never modified
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
