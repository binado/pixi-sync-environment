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

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_success(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_export_output
    ):
        """Test successful export from pixi."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_export_output, stderr="", returncode=0
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

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_invalid_yaml(self, mock_run, mock_check_pixi, tmp_project_dir):
        """Test that PixiError is raised when pixi returns invalid YAML."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout="{ invalid: yaml: :", stderr="", returncode=0
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

    @patch("pixi_sync_environment.pixi_environment.check_pixi_availability")
    @patch("pixi_sync_environment.pixi_environment.subprocess.run")
    def test_export_uses_stdout_output(
        self, mock_run, mock_check_pixi, tmp_project_dir, mock_pixi_export_output
    ):
        """Test that export outputs to stdout using '-' argument."""
        manifest_path = tmp_project_dir / "pixi.toml"
        manifest_path.touch()

        mock_run.return_value = MagicMock(
            stdout=mock_pixi_export_output, stderr="", returncode=0
        )

        export_conda_environment(manifest_path)

        call_args = mock_run.call_args[0][0]
        assert "-" in call_args
