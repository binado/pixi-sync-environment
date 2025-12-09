"""Tests for the pixi_environment module."""

import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from pixi_sync_environment.pixi_environment import (
    PixiError,
    check_pixi_availability,
    export_conda_environment,
)


def mock_pixi_export_with_temp_file(mock_run, mock_export_output):
    """Helper to mock pixi export that uses temporary files."""

    def side_effect(*args, **kwargs):
        # Create a temporary file with the mock output
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as tmp_file:
            tmp_file.write(mock_export_output)
        # Return mock result
        return MagicMock(stdout="", stderr="", returncode=0)

    mock_run.side_effect = side_effect
    return None  # tmp_path is not accessible here, but the file will be created


class TestCheckPixiAvailability:
    """Tests for check_pixi_availability function."""

    @patch("pixi_sync_environment.pixi_environment.shutil.which")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_check_pixi_available(self, mock_run, mock_which):
        """Test that no exception is raised when pixi is available."""
        mock_which.return_value = "/usr/bin/pixi"
        mock_run.return_value = MagicMock(stdout="pixi 0.10.0\n")

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


class TestExportCondaEnvironment:
    """Tests for export_conda_environment function."""

    @patch("pixi_sync_environment.pixi_environment.tempfile.NamedTemporaryFile")
    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_success(
        self,
        mock_run,
        mock_check_pixi,
        mock_temp_file,
        tmp_project_dir,
        mock_pixi_export_output,
    ):
        """Test successful export from pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        # Mock the temporary file
        mock_temp_file.return_value.__enter__ = MagicMock()
        mock_temp_file.return_value.__exit__ = MagicMock()
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.yml"

        # Mock the subprocess result - the temp file will contain our mock output
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        # Mock the file reading to return our expected content
        with patch("builtins.open", return_value=MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                mock_pixi_export_output
            )
            result = export_conda_environment(manifest_path)

        assert "name" in result
        assert "channels" in result
        assert "dependencies" in result
        assert result["name"] == "default"
        mock_check_pixi.assert_called_once()

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_with_environment(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_export_output
    ):
        """Test that --environment flag is passed to pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_export_output, stderr="", returncode=0
        )

        export_conda_environment(manifest_path, environment="dev")

        call_args = mock_run.call_args[0][0]
        assert "--environment" in call_args
        assert "dev" in call_args

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_with_name(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_export_output
    ):
        """Test that --name flag is passed to pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_export_output, stderr="", returncode=0
        )

        export_conda_environment(manifest_path, name="custom-name")

        call_args = mock_run.call_args[0][0]
        assert "--name" in call_args
        assert "custom-name" in call_args

    @patch("pixi_sync_environment.pixi_environment.tempfile.NamedTemporaryFile")
    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_invalid_yaml(
        self, mock_run, mock_check_pixi, mock_temp_file, tmp_project_dir
    ):
        """Test that PixiError is raised when pixi returns invalid YAML."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        # Mock the temporary file
        mock_temp_file.return_value.__enter__ = MagicMock()
        mock_temp_file.return_value.__exit__ = MagicMock()
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.yml"

        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        # Mock the file reading to return invalid YAML
        with patch("builtins.open", return_value=MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                "{ invalid: yaml: :"
            )
            with pytest.raises(PixiError, match="invalid YAML"):
                export_conda_environment(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_command_failed(self, mock_run, mock_check_pixi, tmp_project_dir):
        """Test that PixiError is raised when pixi export fails."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "workspace", "export"])
        error.stdout = ""
        error.stderr = "pixi error"
        mock_run.side_effect = error

        with pytest.raises(PixiError, match="pixi workspace export command failed"):
            export_conda_environment(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_environment_not_found(
        self, mock_run, mock_check_pixi, tmp_project_dir
    ):
        """Test specific error message when environment doesn't exist."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        error = subprocess.CalledProcessError(1, ["pixi", "workspace", "export"])
        error.stdout = ""
        error.stderr = "environment 'dev' not found"
        mock_run.side_effect = error

        with pytest.raises(PixiError, match="Environment 'dev' not found"):
            export_conda_environment(manifest_path, environment="dev")

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    def test_export_manifest_not_found(self, mock_check_pixi, tmp_project_dir):
        """Test that FileNotFoundError is raised for missing manifest."""
        manifest_path = tmp_project_dir / "nonexistent.toml"

        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            export_conda_environment(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_timeout(self, mock_run, mock_check_pixi, tmp_project_dir):
        """Test that PixiError is raised when pixi export times out."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.side_effect = subprocess.TimeoutExpired(
            ["pixi", "workspace", "export"], 60
        )

        with pytest.raises(PixiError, match="timed out"):
            export_conda_environment(manifest_path)

    @patch("pixi_sync_environment.pixi_environment.tempfile.NamedTemporaryFile")
    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_uses_temp_file(
        self,
        mock_run,
        mock_check_pixi,
        mock_temp_file,
        tmp_project_dir,
        mock_pixi_export_output,
    ):
        """Test that export uses temporary file instead of stdout."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        # Mock the temporary file
        mock_temp_file.return_value.__enter__ = MagicMock()
        mock_temp_file.return_value.__exit__ = MagicMock()
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.yml"

        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        # Mock the file reading to return our expected content
        with patch("builtins.open", return_value=MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                mock_pixi_export_output
            )
            export_conda_environment(manifest_path)

        call_args = mock_run.call_args[0][0]
        # Should use temp file path instead of "-"
        assert "-" not in call_args
        assert any(".yml" in arg for arg in call_args if isinstance(arg, str))
