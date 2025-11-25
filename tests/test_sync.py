"""Tests for the core sync functionality."""

from unittest.mock import MagicMock, patch

import pytest

from pixi_sync_environment import pixi_sync_environment
from pixi_sync_environment.pixi_environment import PixiError


class TestPixiSyncEnvironmentFileOperations:
    """Tests for file creation and update operations."""

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_creates_new_file(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that sync creates environment.yml when it doesn't exist."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "test", "dependencies": ["python"]}

        result = pixi_sync_environment(tmp_project_dir)

        assert result is True
        mock_save.assert_called_once()

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_updates_different_file(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that sync updates environment.yml when content differs."""
        mock_load.return_value = {"name": "old", "dependencies": ["python"]}
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "new", "dependencies": ["python=3.10"]}

        result = pixi_sync_environment(tmp_project_dir)

        assert result is True
        mock_save.assert_called_once()

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_preserves_identical_file(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that sync doesn't modify file when content is identical."""
        env_data = {"name": "test", "dependencies": ["python=3.10"]}
        mock_load.return_value = env_data
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = env_data

        result = pixi_sync_environment(tmp_project_dir)

        assert result is True
        mock_save.assert_not_called()


class TestPixiSyncEnvironmentCheckMode:
    """Tests for check mode (read-only) operation."""

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_check_mode_new_file(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test check mode returns False when file doesn't exist."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "test", "dependencies": ["python"]}

        result = pixi_sync_environment(tmp_project_dir, check=True)

        assert result is False
        mock_save.assert_not_called()

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_check_mode_different(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test check mode returns False when files differ."""
        mock_load.return_value = {"name": "old", "dependencies": ["python"]}
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "new", "dependencies": ["python=3.10"]}

        result = pixi_sync_environment(tmp_project_dir, check=True)

        assert result is False
        mock_save.assert_not_called()

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_check_mode_identical(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test check mode returns True when files match."""
        env_data = {"name": "test", "dependencies": ["python=3.10"]}
        mock_load.return_value = env_data
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = env_data

        result = pixi_sync_environment(tmp_project_dir, check=True)

        assert result is True
        mock_save.assert_not_called()

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    def test_sync_check_mode_calls_diff_callback(
        self,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that show_diff_callback is invoked in check mode when out of sync."""
        mock_load.return_value = {"name": "old"}
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "new"}

        callback = MagicMock()
        result = pixi_sync_environment(
            tmp_project_dir, check=True, show_diff_callback=callback
        )

        assert result is False
        callback.assert_called_once()
        call_args = callback.call_args[0]
        assert call_args[0] == {"name": "old"}
        assert call_args[1] == {"name": "new"}
        assert call_args[2] == "environment.yml"

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    def test_sync_check_mode_no_callback_when_synced(
        self,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that callback is not called when files are in sync."""
        env_data = {"name": "test"}
        mock_load.return_value = env_data
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = env_data

        callback = MagicMock()
        result = pixi_sync_environment(
            tmp_project_dir, check=True, show_diff_callback=callback
        )

        assert result is True
        callback.assert_not_called()


class TestPixiSyncEnvironmentErrorHandling:
    """Tests for error handling."""

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    def test_sync_raises_pixi_error(
        self, mock_load, mock_get_manifest, mock_export, tmp_project_dir
    ):
        """Test that PixiError is propagated."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.side_effect = PixiError("pixi failed")

        with pytest.raises(PixiError, match="pixi failed"):
            pixi_sync_environment(tmp_project_dir)

    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    def test_sync_raises_value_error(
        self, mock_load, mock_get_manifest, tmp_project_dir
    ):
        """Test that ValueError is propagated when no manifest found."""
        mock_load.return_value = None
        mock_get_manifest.side_effect = ValueError("No manifest")

        with pytest.raises(ValueError, match="No manifest"):
            pixi_sync_environment(tmp_project_dir)


class TestPixiSyncEnvironmentOptions:
    """Tests for various configuration options."""

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_with_all_options(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that all options are passed through correctly."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"name": "test"}

        pixi_sync_environment(
            tmp_project_dir,
            environment="dev",
            environment_file="custom.yml",
            name="myenv",
        )

        mock_export.assert_called_once()
        call_kwargs = mock_export.call_args[1]
        assert call_kwargs["environment"] == "dev"
        assert call_kwargs["name"] == "myenv"

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_environment_name(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that custom environment is used."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"dependencies": []}

        pixi_sync_environment(tmp_project_dir, environment="dev")

        call_kwargs = mock_export.call_args[1]
        assert call_kwargs["environment"] == "dev"

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_custom_environment_file(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test using a custom environment filename."""
        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = {"dependencies": []}

        pixi_sync_environment(tmp_project_dir, environment_file="custom.yml")

        load_call_args = mock_load.call_args[0]
        assert load_call_args[1] == "custom.yml"

        save_call_kwargs = mock_save.call_args[1]
        assert save_call_kwargs["environment_file"] == "custom.yml"


class TestPixiSyncEnvironmentIdempotency:
    """Tests for idempotent behavior."""

    @patch("pixi_sync_environment.sync.export_conda_environment")
    @patch("pixi_sync_environment.sync.get_manifest_path")
    @patch("pixi_sync_environment.sync.load_environment_file")
    @patch("pixi_sync_environment.sync.save_environment_file")
    def test_sync_idempotent(
        self,
        mock_save,
        mock_load,
        mock_get_manifest,
        mock_export,
        tmp_project_dir,
    ):
        """Test that running sync twice doesn't modify file on second run."""
        env_data = {"name": "test", "dependencies": ["python"]}

        mock_load.return_value = None
        mock_get_manifest.return_value = tmp_project_dir / "pixi.toml"
        mock_export.return_value = env_data

        result1 = pixi_sync_environment(tmp_project_dir)
        assert result1 is True
        assert mock_save.call_count == 1

        mock_load.return_value = env_data
        result2 = pixi_sync_environment(tmp_project_dir)
        assert result2 is True
        assert mock_save.call_count == 1
