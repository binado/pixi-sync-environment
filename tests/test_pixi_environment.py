"""Tests for the pixi_environment module."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pixi_sync_environment.package_info import PackageInfo
from pixi_sync_environment.pixi_environment import (
    PixiError,
    check_pixi_availability,
    create_environment_dict_from_packages,
    create_environment_dict_from_pixi,
    get_pixi_packages,
)


class TestCheckPixiAvailability:
    """Tests for check_pixi_availability function."""

    @patch("pixi_sync_environment.pixi_environment.shutil.which")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_check_pixi_available(self, mock_run, mock_which):
        """Test that no exception is raised when pixi is available."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = MagicMock(stdout="pixi 0.10.0\n")

        # Should not raise
        check_pixi_availability()

        mock_which.assert_called_once_with("pixi")
        mock_run.assert_called_once()

    @patch("pixi_sync_environment.pixi_environment.shutil.which")
    def test_check_pixi_not_found(self, mock_which):
        """Test that PixiError is raised when pixi is not in PATH."""
        mock_which.return_value = None

        with pytest.raises(PixiError, match="pixi command not found"):
            check_pixi_availability()

    @patch("pixi_sync_environment.pixi_environment.shutil.which")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_check_pixi_command_failed(self, mock_run, mock_which):
        """Test that PixiError is raised when pixi --version fails."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["pixi", "--version"], stderr="error message"
        )

        with pytest.raises(PixiError, match="not working properly"):
            check_pixi_availability()

    @patch("pixi_sync_environment.pixi_environment.shutil.which")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_check_pixi_timeout(self, mock_run, mock_which):
        """Test that PixiError is raised when pixi --version times out."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.side_effect = subprocess.TimeoutExpired(["pixi", "--version"], 10)

        with pytest.raises(PixiError, match="timed out"):
            check_pixi_availability()


class TestGetPixiPackages:
    """Tests for get_pixi_packages function."""

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_success(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_list_output
    ):
        """Test successful package retrieval from pixi list."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_list_output, stderr="", returncode=0
        )

        result = get_pixi_packages(manifest_path)

        assert len(result) == 2
        assert all(isinstance(pkg, PackageInfo) for pkg in result)
        assert result[0].name == "python"
        assert result[1].name == "pyyaml"

        mock_check_pixi.assert_called_once()

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_explicit_flag(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_list_output
    ):
        """Test that --explicit flag is passed to pixi list."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_list_output, stderr="", returncode=0
        )

        get_pixi_packages(manifest_path, explicit=True)

        # Check that subprocess.run was called with --explicit
        call_args = mock_run.call_args[0][0]
        assert "--explicit" in call_args

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_environment_specified(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_list_output
    ):
        """Test that --environment flag is passed to pixi list."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_list_output, stderr="", returncode=0
        )

        get_pixi_packages(manifest_path, environment="dev")

        # Check that subprocess.run was called with --environment dev
        call_args = mock_run.call_args[0][0]
        assert "--environment" in call_args
        assert "dev" in call_args

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_invalid_json(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test that PixiError is raised when pixi returns invalid JSON."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout="{ invalid json", stderr="", returncode=0
        )

        with pytest.raises(PixiError, match="invalid JSON"):
            get_pixi_packages(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_command_failed(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test that PixiError is raised when pixi list fails."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "list"])
        error.stdout = ""
        error.stderr = "pixi error"
        mock_run.side_effect = error

        with pytest.raises(PixiError, match="pixi list command failed"):
            get_pixi_packages(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_environment_not_found(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test specific error message when environment doesn't exist."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "list"])
        error.stdout = ""
        error.stderr = "environment 'dev' not found"
        mock_run.side_effect = error

        with pytest.raises(PixiError, match="Environment 'dev' not found"):
            get_pixi_packages(manifest_path, environment="dev")

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    def test_get_pixi_packages_manifest_not_found(
        self, mock_check_pixi, tmp_project_dir
    ):
        """Test that FileNotFoundError is raised for missing manifest."""
        manifest_path = tmp_project_dir / "nonexistent.toml"

        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            get_pixi_packages(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_timeout(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test that PixiError is raised when pixi list times out."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.side_effect = subprocess.TimeoutExpired(["pixi", "list"], 60)

        with pytest.raises(PixiError, match="timed out"):
            get_pixi_packages(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_get_pixi_packages_unexpected_format(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test that PixiError is raised when JSON schema is unexpected."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        # Valid JSON but wrong schema (missing required fields)
        bad_json = json.dumps([{"name": "python"}])  # Missing version, etc.
        mock_run.return_value = MagicMock(stdout=bad_json, stderr="", returncode=0)

        with pytest.raises(PixiError, match="Unexpected package data format"):
            get_pixi_packages(manifest_path)


class TestCreateEnvironmentDictFromPackages:
    """Tests for create_environment_dict_from_packages function."""

    def test_create_dict_conda_only(self, sample_conda_packages):
        """Test creating dict with only conda packages."""
        result = create_environment_dict_from_packages(sample_conda_packages)

        assert "dependencies" in result
        assert all(isinstance(dep, str) for dep in result["dependencies"])
        assert len(result["dependencies"]) == 3

    def test_create_dict_with_pip_packages_included(self, sample_mixed_packages):
        """Test creating dict with include_pip_packages=True."""
        result = create_environment_dict_from_packages(
            sample_mixed_packages, include_pip_packages=True
        )

        assert "dependencies" in result
        # Last item should be pip dict
        pip_deps = result["dependencies"][-1]
        assert isinstance(pip_deps, dict)
        assert "pip" in pip_deps
        assert len(pip_deps["pip"]) == 2

    def test_create_dict_with_pip_packages_excluded(self, sample_mixed_packages):
        """Test creating dict with include_pip_packages=False."""
        result = create_environment_dict_from_packages(
            sample_mixed_packages, include_pip_packages=False
        )

        assert "dependencies" in result
        # Should only have conda packages (all strings)
        assert all(isinstance(dep, str) for dep in result["dependencies"])
        assert len(result["dependencies"]) == 3

    def test_create_dict_with_channels(self, sample_conda_packages):
        """Test that channels are included and deduplicated."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, include_conda_channels=True
        )

        assert "channels" in result
        assert result["channels"] == ["conda-forge"]

    def test_create_dict_without_channels(self, sample_conda_packages):
        """Test creating dict with include_conda_channels=False."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, include_conda_channels=False
        )

        assert "channels" not in result

    def test_create_dict_with_build(self, sample_conda_packages):
        """Test that build strings are included when requested."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, include_build=True
        )

        deps = result["dependencies"]
        assert "python=3.10.0=h1234567_0" in deps
        assert "pyyaml=6.0.1=py310h9876543_0" in deps

    def test_create_dict_without_build(self, sample_conda_packages):
        """Test that build strings are omitted by default."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, include_build=False
        )

        deps = result["dependencies"]
        assert "python=3.10.0" in deps
        assert "pyyaml=6.0.1" in deps

    def test_create_dict_with_name(self, sample_conda_packages):
        """Test that name is included when provided."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, name="my-env"
        )

        assert "name" in result
        assert result["name"] == "my-env"

    def test_create_dict_without_name(self, sample_conda_packages):
        """Test that name is omitted when not provided."""
        result = create_environment_dict_from_packages(sample_conda_packages, name=None)

        assert "name" not in result

    def test_create_dict_with_prefix(self, sample_conda_packages):
        """Test that prefix is included when provided."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, prefix="/path/to/env"
        )

        assert "prefix" in result
        assert result["prefix"] == "/path/to/env"

    def test_create_dict_without_prefix(self, sample_conda_packages):
        """Test that prefix is omitted when not provided."""
        result = create_environment_dict_from_packages(
            sample_conda_packages, prefix=None
        )

        assert "prefix" not in result

    def test_create_dict_channel_order_preserved(self):
        """Test that channel order is preserved (first seen first)."""
        packages = [
            PackageInfo(
                name="pkg1",
                version="1.0",
                size_bytes=100,
                build="h1",
                kind="conda",
                source="conda-forge",
                is_explicit=True,
            ),
            PackageInfo(
                name="pkg2",
                version="2.0",
                size_bytes=200,
                build="h2",
                kind="conda",
                source="defaults",
                is_explicit=True,
            ),
            PackageInfo(
                name="pkg3",
                version="3.0",
                size_bytes=300,
                build="h3",
                kind="conda",
                source="conda-forge",  # Duplicate, should be ignored
                is_explicit=True,
            ),
        ]

        result = create_environment_dict_from_packages(
            packages, include_conda_channels=True
        )

        assert result["channels"] == ["conda-forge", "defaults"]

    def test_create_dict_empty_packages(self):
        """Test creating dict with empty package list."""
        result = create_environment_dict_from_packages([])

        assert "dependencies" in result
        assert result["dependencies"] == []
        assert "channels" not in result  # No packages, no channels

    def test_create_dict_all_options(self, sample_mixed_packages):
        """Test creating dict with all options enabled."""
        result = create_environment_dict_from_packages(
            sample_mixed_packages,
            name="full-env",
            prefix="/opt/env",
            include_pip_packages=True,
            include_conda_channels=True,
            include_build=True,
        )

        assert result["name"] == "full-env"
        assert result["prefix"] == "/opt/env"
        assert "channels" in result
        assert isinstance(result["dependencies"][-1], dict)
        assert "pip" in result["dependencies"][-1]
        # Check build strings in conda packages
        assert any(
            "=" in dep and dep.count("=") == 2
            for dep in result["dependencies"]
            if isinstance(dep, str)
        )


class TestCreateEnvironmentDictFromPixi:
    """Tests for create_environment_dict_from_pixi function."""

    @patch("pixi_sync_environment.pixi_environment.get_pixi_packages")
    def test_create_dict_from_pixi_integration(
        self, mock_get_packages, tmp_project_dir, sample_conda_packages
    ):
        """Test that create_environment_dict_from_pixi combines functions correctly."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_get_packages.return_value = sample_conda_packages

        result = create_environment_dict_from_pixi(
            manifest_path, "default", name="test-env"
        )

        mock_get_packages.assert_called_once_with(
            manifest_path, "default", explicit=False
        )
        assert "dependencies" in result
        assert result.get("name") == "test-env"

    @patch("pixi_sync_environment.pixi_environment.get_pixi_packages")
    def test_create_dict_from_pixi_propagates_errors(
        self, mock_get_packages, tmp_project_dir
    ):
        """Test that PixiError from get_pixi_packages is propagated."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_get_packages.side_effect = PixiError("test error")

        with pytest.raises(PixiError, match="test error"):
            create_environment_dict_from_pixi(manifest_path, "default")

    @patch("pixi_sync_environment.pixi_environment.get_pixi_packages")
    def test_create_dict_from_pixi_passes_all_options(
        self, mock_get_packages, tmp_project_dir, sample_mixed_packages
    ):
        """Test that all options are passed through correctly."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_get_packages.return_value = sample_mixed_packages

        result = create_environment_dict_from_pixi(
            manifest_path,
            "dev",
            explicit=True,
            name="dev-env",
            prefix="/opt/dev",
            include_pip_packages=True,
            include_conda_channels=True,
            include_build=True,
        )

        mock_get_packages.assert_called_once_with(manifest_path, "dev", explicit=True)
        assert result["name"] == "dev-env"
        assert result["prefix"] == "/opt/dev"
        assert "channels" in result
