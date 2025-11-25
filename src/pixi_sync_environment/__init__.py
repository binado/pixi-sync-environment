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

from pixi_sync_environment.pixi_environment import PixiError
from pixi_sync_environment.sync import pixi_sync_environment

__all__ = ["pixi_sync_environment", "PixiError"]
