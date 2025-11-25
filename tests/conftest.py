"""Pytest configuration and shared fixtures."""

import pytest


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
def mock_pixi_export_output():
    """Create mock YAML output from pixi workspace export command.

    Returns
    -------
    str
        YAML string representing pixi workspace export output.
    """
    return """name: default
channels:
- conda-forge
- nodefaults
dependencies:
- python >=3.10
- pyyaml >=6.0
"""


@pytest.fixture
def mock_pixi_export_dict():
    """Create mock dict output from pixi workspace export command.

    Returns
    -------
    dict
        Dictionary representing parsed pixi workspace export output.
    """
    return {
        "name": "default",
        "channels": ["conda-forge", "nodefaults"],
        "dependencies": ["python >=3.10", "pyyaml >=6.0"],
    }
