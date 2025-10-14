from dataclasses import dataclass
from typing import Literal


@dataclass
class PackageInfo:
    """Information about a package from pixi list output.

    This class represents package metadata extracted from pixi's package listing,
    supporting both conda and PyPI packages with their associated metadata.

    Parameters
    ----------
    name : str
        The package name.
    version : str
        The package version string.
    size_bytes : int
        The package size in bytes.
    build : str or None
        The build string for conda packages, None for PyPI packages.
    kind : {"conda", "pypi"}
        The package type, either "conda" or "pypi".
    source : str
        The source/channel where the package originates from.
    is_explicit : bool
        Whether the package was explicitly requested or is a dependency.
    is_editable : bool or None, optional
        Whether the package is installed in editable mode (mainly for PyPI packages).
        Default is None.

    Examples
    --------
    >>> pkg = PackageInfo(
    ...     name="numpy",
    ...     version="1.24.0",
    ...     size_bytes=12345678,
    ...     build="py311h1234567_0",
    ...     kind="conda",
    ...     source="conda-forge",
    ...     is_explicit=True
    ... )
    >>> pkg.get_package_spec_str()
    'numpy=1.24.0'
    >>> pkg.get_package_spec_str(include_build=True)
    'numpy=1.24.0=py311h1234567_0'
    """

    name: str
    version: str
    size_bytes: int
    build: str | None
    kind: Literal["conda", "pypi"]
    source: str
    is_explicit: bool
    is_editable: bool | None = None

    @property
    def is_conda_package(self) -> bool:
        """Check if this is a conda package.

        Returns
        -------
        bool
            True if this is a conda package, False otherwise.
        """
        return self.kind == "conda"

    @property
    def is_pypi_package(self) -> bool:
        """Check if this is a PyPI package.

        Returns
        -------
        bool
            True if this is a PyPI package, False otherwise.
        """
        return self.kind == "pypi"

    def get_package_spec_str(self, include_build: bool = False) -> str:
        """Generate a package specification string for conda environments.

        Creates a package specification string in the format expected by conda
        environment files, optionally including build information.

        Parameters
        ----------
        include_build : bool, optional
            Whether to include build information in the specification.
            Only applies to conda packages with build information.
            Default is False.

        Returns
        -------
        str
            Package specification string in format "name=version" or
            "name=version=build" if include_build is True and build exists.

        Examples
        --------
        >>> pkg = PackageInfo(name="numpy", version="1.24.0", build="py311_0", ...)
        >>> pkg.get_package_spec_str()
        'numpy=1.24.0'
        >>> pkg.get_package_spec_str(include_build=True)
        'numpy=1.24.0=py311_0'
        """
        properties = [self.name, self.version]
        if include_build and self.build is not None:
            properties.append(self.build)
        return "=".join(properties)
