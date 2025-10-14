"""Pixi environment integration and package management.

This module provides functions for interacting with pixi environments,
retrieving package information, and creating conda environment dictionaries.
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

from pixi_sync_environment.package_info import PackageInfo

logger = logging.getLogger(__name__)


class PixiError(Exception):
    """Exception raised when pixi command operations fail.

    Attributes
    ----------
    message : str
        The error message.
    stdout : str, optional
        Standard output from the failed command.
    stderr : str, optional
        Standard error output from the failed command.
    """

    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(self.message)


def check_pixi_availability() -> None:
    """Check if pixi command is available and accessible.

    Raises
    ------
    PixiError
        If pixi command is not found or not executable.

    Examples
    --------
    >>> check_pixi_availability()  # doctest: +SKIP
    # No output if pixi is available
    """
    if not shutil.which("pixi"):
        raise PixiError(
            "pixi command not found. Please install pixi first. "
            "Visit https://pixi.sh for installation instructions."
        )

    try:
        result = subprocess.run(
            ["pixi", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        logger.debug(f"Found pixi version: {result.stdout.strip()}")
    except subprocess.CalledProcessError as err:
        raise PixiError(
            f"pixi command is not working properly: {err.stderr}",
            stdout=err.stdout,
            stderr=err.stderr,
        ) from err
    except subprocess.TimeoutExpired as err:
        raise PixiError(
            "pixi command timed out - this may indicate an installation issue"
        ) from err
    except FileNotFoundError as err:
        raise PixiError("pixi command not found. Please install pixi first.") from err


def get_pixi_packages(
    manifest_path: Path, environment: str | None = None, explicit: bool = False
) -> list[PackageInfo]:
    """Retrieve package information from a pixi environment.

    Executes 'pixi list' command to get package information from the specified
    pixi environment and parses the JSON output into PackageInfo objects.

    Parameters
    ----------
    manifest_path : Path
        Path to the pixi manifest file (pixi.toml or pyproject.toml).
    environment : str or None, optional
        Name of the pixi environment to query. If None, uses the default
        environment. Default is None.
    explicit : bool, optional
        Whether to return only explicitly requested packages (not dependencies).
        Default is False.

    Returns
    -------
    list of PackageInfo
        List of package information objects for all packages in the environment.

    Raises
    ------
    PixiError
        If the pixi command fails or returns invalid output.
    json.JSONDecodeError
        If the pixi command output is not valid JSON.
    FileNotFoundError
        If the manifest path does not exist.

    Examples
    --------
    >>> manifest = Path("/project/pixi.toml")
    >>> packages = get_pixi_packages(manifest)  # doctest: +SKIP
    >>> len(packages) > 0
    True

    >>> packages = get_pixi_packages(manifest, environment="dev")  # doctest: +SKIP
    """
    # First check if pixi is available
    check_pixi_availability()

    # Validate manifest path
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    logger.info("Getting packages from pixi environment '%s'", environment or "default")
    args = [
        "pixi",
        "list",
        "--manifest-path",
        str(manifest_path),
        "--json",
    ]
    if environment:
        args += ["--environment", environment]
    if explicit:
        args.append("--explicit")

    cmd = " ".join(args)
    logger.info("Running: %s", cmd)

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,  # Add timeout to prevent hanging
        )
    except subprocess.CalledProcessError as err:
        logger.error("pixi command failed with code %d", err.returncode)
        logger.error("stdout: %s", err.stdout)
        logger.error("stderr: %s", err.stderr)

        # Provide more specific error messages based on common failure modes
        if "environment" in err.stderr.lower() and environment:
            raise PixiError(
                f"Environment '{environment}' not found in pixi manifest. "
                f"Available environments can be listed with 'pixi info'.",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err
        elif "manifest" in err.stderr.lower():
            raise PixiError(
                f"Invalid or corrupted pixi manifest at {manifest_path}",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err
        else:
            raise PixiError(
                f"pixi list command failed: {err.stderr}",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err

    except subprocess.TimeoutExpired as err:
        raise PixiError(
            "pixi list command timed out after 60 seconds. "
            "This may indicate a very large environment or network issues."
        ) from err

    # Parse JSON output
    try:
        package_list = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        logger.error("Invalid JSON output from pixi: %s", result.stdout[:200])
        raise PixiError(
            f"pixi command returned invalid JSON: {err}",
            stdout=result.stdout,
            stderr=result.stderr,
        ) from err

    # Convert to PackageInfo objects
    try:
        packages = [PackageInfo(**package) for package in package_list]
        logger.info("Retrieved %d packages from pixi environment", len(packages))
        return packages
    except (TypeError, ValueError) as err:
        logger.error("Failed to parse package data: %s", err)
        raise PixiError(
            f"Unexpected package data format from pixi: {err}", stdout=result.stdout
        ) from err


def create_environment_dict_from_packages(
    packages: Iterable[PackageInfo],
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
) -> dict[str, Any]:
    """Create a conda environment dictionary from package information.

    Transforms package information into a dictionary structure suitable for
    conda environment.yml files, with options to control what information
    is included.

    Parameters
    ----------
    packages : Iterable of PackageInfo
        Collection of package information objects to include in the environment.
    name : str or None, optional
        Environment name to include in the dictionary. If None, no name is set.
        Default is None.
    prefix : str or None, optional
        Environment prefix path to include. If None, no prefix is set.
        Default is None.
    include_pip_packages : bool, optional
        Whether to include PyPI packages in the dependencies section.
        Default is False.
    include_conda_channels : bool, optional
        Whether to include conda channels in the environment specification.
        Default is True.
    include_build : bool, optional
        Whether to include build strings in conda package specifications.
        Default is False.

    Returns
    -------
    dict
        Dictionary suitable for serializing to conda environment.yml format.
        Contains keys like 'name', 'channels', 'dependencies', 'prefix' as applicable.

    Examples
    --------
    >>> packages = [PackageInfo(name="numpy", version="1.24.0", ...)]
    >>> env_dict = create_environment_dict_from_packages(packages, name="myenv")
    >>> 'dependencies' in env_dict
    True
    >>> env_dict['name']
    'myenv'

    Notes
    -----
    - Conda packages are listed directly in the dependencies array
    - PyPI packages are nested under a 'pip' key if included
    - Channels are deduplicated from conda package sources
    - Build information is only included for conda packages when requested
    """
    conda_packages = [package for package in packages if package.is_conda_package]
    pypi_packages = [package for package in packages if package.is_pypi_package]

    # Build conda package specifications
    dependencies: list[str | dict[str, Any]] = [
        package.get_package_spec_str(include_build=include_build)
        for package in conda_packages
    ]

    # Add PyPI packages if requested
    if pypi_packages and include_pip_packages:
        pypi_package_specs = [
            package.get_package_spec_str(include_build=False)
            for package in pypi_packages
        ]
        dependencies.append({"pip": pypi_package_specs})

    # Build environment dictionary
    environment_dict: dict[str, Any] = {}

    if name is not None:
        environment_dict["name"] = name

    if prefix is not None:
        environment_dict["prefix"] = prefix

    if include_conda_channels and conda_packages:
        # Deduplicate channels while preserving order
        channels = list(dict.fromkeys(package.source for package in conda_packages))
        environment_dict["channels"] = channels

    environment_dict["dependencies"] = dependencies

    return environment_dict


def create_environment_dict_from_pixi(
    manifest_path: Path,
    environment: str,
    explicit: bool = False,
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
) -> dict[str, Any]:
    """Create a conda environment dictionary from a pixi environment.

    This is a convenience function that combines getting packages from pixi
    with creating an environment dictionary, providing a single-step conversion
    from pixi to conda format.

    Parameters
    ----------
    manifest_path : Path
        Path to the pixi manifest file (pixi.toml or pyproject.toml).
    environment : str
        Name of the pixi environment to convert.
    explicit : bool, optional
        Whether to include only explicitly requested packages (not dependencies).
        Default is False.
    name : str or None, optional
        Environment name to include in the dictionary. If None, no name is set.
        Default is None.
    prefix : str or None, optional
        Environment prefix path to include. If None, no prefix is set.
        Default is None.
    include_pip_packages : bool, optional
        Whether to include PyPI packages in the dependencies section.
        Default is False.
    include_conda_channels : bool, optional
        Whether to include conda channels in the environment specification.
        Default is True.
    include_build : bool, optional
        Whether to include build strings in conda package specifications.
        Default is False.

    Returns
    -------
    dict
        Dictionary suitable for serializing to conda environment.yml format.
        Contains keys like 'name', 'channels', 'dependencies', 'prefix' as applicable.

    Raises
    ------
    PixiError
        If the pixi command fails or returns invalid output.
    FileNotFoundError
        If the manifest path does not exist.
    json.JSONDecodeError
        If the pixi command output is not valid JSON.

    Examples
    --------
    >>> manifest = Path("/project/pixi.toml")
    >>> env_dict = create_environment_dict_from_pixi(  # doctest: +SKIP
    ...     manifest, "default", name="myenv"
    ... )
    >>> env_dict["name"]  # doctest: +SKIP
    'myenv'

    >>> # Include only explicit packages with build info
    >>> env_dict = create_environment_dict_from_pixi(  # doctest: +SKIP
    ...     manifest, "dev", explicit=True, include_build=True
    ... )

    See Also
    --------
    get_pixi_packages : Get package information from pixi environment
    create_environment_dict_from_packages : Create environment dict from packages
    """
    packages = get_pixi_packages(manifest_path, environment, explicit=explicit)
    return create_environment_dict_from_packages(
        packages,
        name=name,
        prefix=prefix,
        include_pip_packages=include_pip_packages,
        include_conda_channels=include_conda_channels,
        include_build=include_build,
    )
