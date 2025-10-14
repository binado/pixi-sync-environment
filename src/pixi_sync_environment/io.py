"""File I/O operations for pixi-sync-environment.

This module provides functions for reading and writing configuration files,
including pixi manifests and conda environment files.
"""

from pathlib import Path
from typing import Any

import yaml

#: Valid pixi manifest filenames in order of preference
MANIFEST_FILENAMES = ("pixi.toml", "pyproject.toml")

#: All valid configuration filenames that can trigger the sync process
CONFIG_FILENAMES = (*MANIFEST_FILENAMES, "environment.yml", "pixi.lock")


def find_project_dir(input_files: list[Path]) -> list[Path]:
    """Extract unique project directories from input files.

    Validates that all input files are recognized configuration files and
    returns their parent directories without duplicates.

    Parameters
    ----------
    input_files : list of Path
        List of file paths to process. Each file must have a filename
        that matches one of the recognized configuration file types.

    Returns
    -------
    list of Path
        Unique list of parent directories containing the input files.

    Raises
    ------
    ValueError
        If any input file has a filename not in CONFIG_FILENAMES.

    Examples
    --------
    >>> files = [Path("/project/pixi.toml"), Path("/project/environment.yml")]
    >>> find_project_dir(files)
    [Path('/project')]

    >>> files = [Path("/proj1/pixi.toml"), Path("/proj2/pixi.toml")]
    >>> find_project_dir(files)
    [Path('/proj1'), Path('/proj2')]
    """
    path_dir = set()
    for input_file in input_files:
        filename = input_file.name
        if filename not in CONFIG_FILENAMES:
            raise ValueError(f"Expected filename to be one of {CONFIG_FILENAMES}")
        path_dir.add(input_file.parent)
    return list(path_dir)


def get_manifest_path(path_dir: Path) -> Path:
    """Find the pixi manifest file in a directory.

    Searches for pixi manifest files in the specified directory in order of
    preference: pixi.toml first, then pyproject.toml.

    Parameters
    ----------
    path_dir : Path
        Directory to search for manifest files.

    Returns
    -------
    Path
        Path to the first found manifest file.

    Raises
    ------
    ValueError
        If no manifest file is found in the directory.

    Examples
    --------
    >>> get_manifest_path(Path("/project"))  # doctest: +SKIP
    Path('/project/pixi.toml')
    """
    for manifest_filename in MANIFEST_FILENAMES:
        manifest_path = path_dir / manifest_filename
        if manifest_path.is_file():
            return manifest_path

    raise ValueError(f"Could not find manifest path on directory {path_dir}")


def load_environment_file(
    path_dir: Path,
    environment_file: str = "environment.yml",
    raise_exception: bool = True,
) -> dict[str, Any] | list[Any] | None:
    """Load a YAML environment file.

    Attempts to load and parse a YAML environment file from the specified
    directory. Can optionally suppress FileNotFoundError exceptions.

    Parameters
    ----------
    path_dir : Path
        Directory containing the environment file.
    environment_file : str, optional
        Name of the environment file to load. Default is "environment.yml".
    raise_exception : bool, optional
        Whether to raise FileNotFoundError if the file doesn't exist.
        If False, returns None instead. Default is True.

    Returns
    -------
    dict or list or None
        Parsed YAML content as a dictionary or list, or None if the file
        doesn't exist and raise_exception is False.

    Raises
    ------
    FileNotFoundError
        If the environment file doesn't exist and raise_exception is True.
    yaml.YAMLError
        If the YAML file is malformed and cannot be parsed.

    Examples
    --------
    >>> load_environment_file(Path("/project"))  # doctest: +SKIP
    {'name': 'myenv', 'dependencies': ['python=3.9']}

    >>> load_environment_file(Path("/missing"), raise_exception=False)
    None
    """
    filepath = path_dir / environment_file
    try:
        with open(filepath, encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError as err:
        if not raise_exception:
            return None
        raise err


def save_environment_file(
    data: dict[str, Any] | list[Any],
    path_dir: Path,
    environment_file: str = "environment.yml",
) -> None:
    """Save data to a YAML environment file.

    Writes the provided data structure to a YAML file with consistent
    formatting suitable for conda environment files.

    Parameters
    ----------
    data : dict or list
        Data structure to serialize to YAML. Typically a dictionary
        containing environment specification.
    path_dir : Path
        Directory where the environment file should be saved.
    environment_file : str, optional
        Name of the environment file to create/overwrite.
        Default is "environment.yml".

    Examples
    --------
    >>> env_data = {'name': 'test', 'dependencies': ['python=3.9']}
    >>> save_environment_file(env_data, Path("/project"))  # doctest: +SKIP

    Notes
    -----
    The YAML output is formatted with:
    - 2-space indentation
    - UTF-8 encoding
    - No flow style (block style only)
    - Preserved key order
    - Unicode support enabled
    """
    filepath = path_dir / environment_file
    with open(filepath, mode="w", encoding="utf-8") as file:
        yaml.dump(
            data,
            file,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
            sort_keys=False,
        )
