"""Tests for the pixi_environment module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pixi_sync_environment.pixi_environment import (
    PixiError,
    check_pixi_availability,
    export_conda_environment,
)


class TestCheckPixiAvailability:
    """Tests for check_pixi_availability function."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the lru_cache before each test."""
        check_pixi_availability.cache_clear()
        yield

    @pytest.fixture
    def availability_mocks(self):
        """Fixture for mocking dependencies of check_pixi_availability."""
        with (
            patch("pixi_sync_environment.pixi_environment.shutil.which") as mock_which,
            patch("pixi_sync_environment.pixi_environment.subprocess.run") as mock_run,
        ):
            yield {"which": mock_which, "run": mock_run}

    def test_check_pixi_available(self, availability_mocks):
        """Test that no exception is raised when pixi is available."""
        availability_mocks["which"].return_value = "/usr/bin/pixi"
        availability_mocks["run"].return_value = MagicMock(stdout="pixi 0.10.0\n")

        check_pixi_availability()

        availability_mocks["which"].assert_called_once_with("pixi")
        availability_mocks["run"].assert_called_once()

    def test_check_pixi_not_found(self, availability_mocks):
        """Test that PixiError is raised when pixi is not in PATH."""
        availability_mocks["which"].return_value = None

        with pytest.raises(PixiError, match="pixi command not found"):
            check_pixi_availability()

    def test_check_pixi_command_failed(self, availability_mocks):
        """Test that PixiError is raised when pixi --version fails."""
        availability_mocks["which"].return_value = "/usr/bin/pixi"
        availability_mocks["run"].side_effect = subprocess.CalledProcessError(
            1, ["pixi", "--version"], stderr="error message"
        )

        with pytest.raises(PixiError, match="not working properly"):
            check_pixi_availability()

    def test_check_pixi_timeout(self, availability_mocks):
        """Test that PixiError is raised when pixi --version times out."""
        availability_mocks["which"].return_value = "/usr/bin/pixi"
        availability_mocks["run"].side_effect = subprocess.TimeoutExpired(
            ["pixi", "--version"], 10
        )

        with pytest.raises(PixiError, match="timed out"):
            check_pixi_availability()


class TestExportCondaEnvironment:
    """Tests for export_conda_environment function."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache to ensure checks run if needed."""
        check_pixi_availability.cache_clear()
        yield

    @pytest.fixture
    def export_mocks(self):
        """Fixture for mocking dependencies of export_conda_environment."""
        with (
            patch(
                "pixi_sync_environment.pixi_environment.tempfile.TemporaryDirectory"
            ) as mock_temp,
            patch(
                "pixi_sync_environment.pixi_environment.check_pixi_availability"
            ) as mock_check,
            patch("pixi_sync_environment.pixi_environment.subprocess.run") as mock_run,
        ):
            yield {"temp": mock_temp, "check": mock_check, "run": mock_run}

    def test_export_success(
        self,
        export_mocks,
        tmp_project_dir,
        mock_pixi_export_output,
        tmp_path,
    ):
        """Test successful export from pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        # Mock TemporaryDirectory to return tmp_path
        export_mocks["temp"].return_value.__enter__.return_value = str(tmp_path)

        # When subprocess runs, create the file (simulating pixi)
        def side_effect(*args, **kwargs):
            (tmp_path / "env.yml").write_text(mock_pixi_export_output)
            return MagicMock(stdout="", stderr="", returncode=0)

        export_mocks["run"].side_effect = side_effect

        result = export_conda_environment(manifest_path)

        assert "name" in result
        assert "channels" in result
        assert "dependencies" in result
        assert result["name"] == "default"
        export_mocks["check"].assert_called_once()

    def test_export_with_environment(
        self,
        export_mocks,
        tmp_project_dir,
        mock_pixi_export_output,
        tmp_path,
    ):
        """Test that --environment flag is passed to pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        export_mocks["temp"].return_value.__enter__.return_value = str(tmp_path)

        def side_effect(*args, **kwargs):
            (tmp_path / "env.yml").write_text(mock_pixi_export_output)
            return MagicMock(stdout="", stderr="", returncode=0)

        export_mocks["run"].side_effect = side_effect

        export_conda_environment(manifest_path, environment="dev")

        call_args = export_mocks["run"].call_args[0][0]
        assert "--environment" in call_args
        assert "dev" in call_args

    def test_export_with_name(
        self,
        export_mocks,
        tmp_project_dir,
        mock_pixi_export_output,
        tmp_path,
    ):
        """Test that --name flag is passed to pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        export_mocks["temp"].return_value.__enter__.return_value = str(tmp_path)

        def side_effect(*args, **kwargs):
            (tmp_path / "env.yml").write_text(mock_pixi_export_output)
            return MagicMock(stdout="", stderr="", returncode=0)

        export_mocks["run"].side_effect = side_effect

        export_conda_environment(manifest_path, name="custom-name")

        call_args = export_mocks["run"].call_args[0][0]
        assert "--name" in call_args
        assert "custom-name" in call_args

    def test_export_invalid_yaml(self, export_mocks, tmp_project_dir, tmp_path):
        """Test that PixiError is raised when pixi returns invalid YAML."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        export_mocks["temp"].return_value.__enter__.return_value = str(tmp_path)

        def side_effect(*args, **kwargs):
            (tmp_path / "env.yml").write_text("{ invalid: yaml: :")
            return MagicMock(stdout="", stderr="", returncode=0)

        export_mocks["run"].side_effect = side_effect

        with pytest.raises(PixiError, match="invalid YAML"):
            export_conda_environment(manifest_path)

    def test_export_command_failed(self, export_mocks, tmp_project_dir):
        """Test that PixiError is raised when pixi export fails."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "workspace", "export"])
        error.stdout = ""
        error.stderr = "pixi error"
        export_mocks["run"].side_effect = error

        with pytest.raises(PixiError, match="pixi workspace export command failed"):
            export_conda_environment(manifest_path)

    def test_export_environment_not_found(self, export_mocks, tmp_project_dir):
        """Test specific error message when environment doesn't exist."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "workspace", "export"])
        error.stdout = ""
        error.stderr = "environment 'dev' not found"
        export_mocks["run"].side_effect = error

        with pytest.raises(PixiError, match="Environment 'dev' not found"):
            export_conda_environment(manifest_path, environment="dev")

    def test_export_manifest_not_found(self, export_mocks, tmp_project_dir):
        """Test that FileNotFoundError is raised for missing manifest."""
        manifest_path = tmp_project_dir / "nonexistent.toml"

        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            export_conda_environment(manifest_path)

    def test_export_timeout(self, export_mocks, tmp_project_dir):
        """Test that PixiError is raised when pixi export times out."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        export_mocks["run"].side_effect = subprocess.TimeoutExpired(
            ["pixi", "workspace", "export"], 60
        )

        with pytest.raises(PixiError, match="timed out"):
            export_conda_environment(manifest_path)

    def test_export_uses_temp_file(
        self,
        export_mocks,
        tmp_project_dir,
        mock_pixi_export_output,
        tmp_path,
    ):
        """Test that export uses temporary file instead of stdout."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        export_mocks["temp"].return_value.__enter__.return_value = str(tmp_path)

        def side_effect(*args, **kwargs):
            (tmp_path / "env.yml").write_text(mock_pixi_export_output)
            return MagicMock(stdout="", stderr="", returncode=0)

        export_mocks["run"].side_effect = side_effect

        export_conda_environment(manifest_path)

        call_args = export_mocks["run"].call_args[0][0]
        # Should use temp file path
        expected_path = str(tmp_path / "env.yml")
        assert expected_path in call_args
