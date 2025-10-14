"""Pytest configuration and shared fixtures."""

import json

import pytest

from pixi_sync_environment.package_info import PackageInfo


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary directory for test projects.

    Parameters
    ----------
    tmp_path : Path
        pytest's temporary directory fixture.

    Returns
    -------
    Path
        Path to a temporary project directory.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def sample_pixi_toml(tmp_project_dir):
    """Create a sample pixi.toml file.

    Parameters
    ----------
    tmp_project_dir : Path
        Temporary project directory.

    Returns
    -------
    Path
        Path to the created pixi.toml file.
    """
    pixi_toml = tmp_project_dir / "pixi.toml"
    pixi_toml.write_text(
        """[project]
name = "test-project"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64"]

[dependencies]
python = ">=3.10"
pyyaml = ">=6.0"
"""
    )
    return pixi_toml


@pytest.fixture
def sample_pyproject_toml(tmp_project_dir):
    """Create a sample pyproject.toml file with pixi config.

    Parameters
    ----------
    tmp_project_dir : Path
        Temporary project directory.

    Returns
    -------
    Path
        Path to the created pyproject.toml file.
    """
    pyproject_toml = tmp_project_dir / "pyproject.toml"
    pyproject_toml.write_text(
        """[project]
name = "test-project"

[tool.pixi.project]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.pixi.dependencies]
python = ">=3.10"
pyyaml = ">=6.0"
"""
    )
    return pyproject_toml


@pytest.fixture
def sample_environment_yml(tmp_project_dir):
    """Create a sample environment.yml file.

    Parameters
    ----------
    tmp_project_dir : Path
        Temporary project directory.

    Returns
    -------
    Path
        Path to the created environment.yml file.
    """
    env_file = tmp_project_dir / "environment.yml"
    env_file.write_text(
        """name: test-env
channels:
- conda-forge
dependencies:
- python=3.10.0
- pyyaml=6.0.1
"""
    )
    return env_file


@pytest.fixture
def sample_conda_packages():
    """Create a list of sample conda PackageInfo objects.

    Returns
    -------
    list[PackageInfo]
        List of conda packages.
    """
    return [
        PackageInfo(
            name="python",
            version="3.10.0",
            size_bytes=12345678,
            build="h1234567_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        ),
        PackageInfo(
            name="pyyaml",
            version="6.0.1",
            size_bytes=234567,
            build="py310h9876543_0",
            kind="conda",
            source="conda-forge",
            is_explicit=True,
        ),
        PackageInfo(
            name="libffi",
            version="3.4.2",
            size_bytes=56789,
            build="h0987654_5",
            kind="conda",
            source="conda-forge",
            is_explicit=False,
        ),
    ]


@pytest.fixture
def sample_pypi_packages():
    """Create a list of sample PyPI PackageInfo objects.

    Returns
    -------
    list[PackageInfo]
        List of PyPI packages.
    """
    return [
        PackageInfo(
            name="requests",
            version="2.31.0",
            size_bytes=123456,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=True,
        ),
        PackageInfo(
            name="urllib3",
            version="2.0.7",
            size_bytes=98765,
            build=None,
            kind="pypi",
            source="https://pypi.org/simple",
            is_explicit=False,
        ),
    ]


@pytest.fixture
def sample_mixed_packages(sample_conda_packages, sample_pypi_packages):
    """Create a list of mixed conda and PyPI packages.

    Parameters
    ----------
    sample_conda_packages : list[PackageInfo]
        Conda packages fixture.
    sample_pypi_packages : list[PackageInfo]
        PyPI packages fixture.

    Returns
    -------
    list[PackageInfo]
        Combined list of packages.
    """
    return sample_conda_packages + sample_pypi_packages


@pytest.fixture
def mock_pixi_list_output():
    """Create mock JSON output from pixi list command.

    Returns
    -------
    str
        JSON string representing pixi list output.
    """
    packages = [
        {
            "name": "python",
            "version": "3.10.0",
            "size_bytes": 12345678,
            "build": "h1234567_0",
            "kind": "conda",
            "source": "conda-forge",
            "is_explicit": True,
        },
        {
            "name": "pyyaml",
            "version": "6.0.1",
            "size_bytes": 234567,
            "build": "py310h9876543_0",
            "kind": "conda",
            "source": "conda-forge",
            "is_explicit": True,
        },
    ]
    return json.dumps(packages)
