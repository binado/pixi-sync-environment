"""Tests for the core sync functionality."""

from unittest.mock import MagicMock, patch

import pytest
import yaml

from pixi_sync_environment import pixi_sync_environment
from pixi_sync_environment.pixi_environment import PixiError


@pytest.fixture
def export_mock():
    """Fixture to mock export_conda_environment."""
    with patch("pixi_sync_environment.sync.export_conda_environment") as mock:
        yield mock


@pytest.mark.parametrize(
    "initial_content, exported_content",
    [
        (None, {"name": "new", "dependencies": ["python"]}),  # New file
        (
            {"name": "old", "dependencies": ["python"]},
            {"name": "new", "dependencies": ["python", "pip"]},
        ),  # Update
        (
            {"name": "same", "dependencies": ["python"]},
            {"name": "same", "dependencies": ["python"]},
        ),  # No change
    ],
)
def test_sync_operations(
    tmp_project_dir,
    sample_pixi_toml,
    export_mock,
    initial_content,
    exported_content,
):
    """Test sync operations (create, update, no-op) with real files."""
    # Setup initial state
    if initial_content:
        env_file = tmp_project_dir / "environment.yml"
        env_file.write_text(yaml.dump(initial_content))

    # Mock the export
    export_mock.return_value = exported_content

    # Run sync
    result = pixi_sync_environment(tmp_project_dir)

    assert result is True

    # Verify result on disk
    env_file = tmp_project_dir / "environment.yml"
    assert env_file.exists()

    with open(env_file) as f:
        saved_content = yaml.safe_load(f)

    assert saved_content == exported_content


@pytest.mark.parametrize(
    "initial_content, exported_content, expected_result",
    [
        (None, {"name": "new"}, False),  # Missing file -> False
        (
            {"name": "old"},
            {"name": "new"},
            False,
        ),  # Different content -> False
        (
            {"name": "same"},
            {"name": "same"},
            True,
        ),  # Same content -> True
    ],
)
def test_sync_check_mode(
    tmp_project_dir,
    sample_pixi_toml,
    export_mock,
    initial_content,
    exported_content,
    expected_result,
):
    """Test check mode behavior without modifying files."""
    # Setup initial state
    if initial_content:
        env_file = tmp_project_dir / "environment.yml"
        env_file.write_text(yaml.dump(initial_content))

    # Mock the export
    export_mock.return_value = exported_content

    # Run sync in check mode
    result = pixi_sync_environment(tmp_project_dir, check=True)

    assert result == expected_result

    # Verify NO changes on disk
    env_file = tmp_project_dir / "environment.yml"
    if initial_content is None:
        assert not env_file.exists()
    else:
        with open(env_file) as f:
            current_content = yaml.safe_load(f)
        assert current_content == initial_content


def test_sync_check_mode_calls_diff_callback(
    tmp_project_dir, sample_pixi_toml, export_mock
):
    """Test that callback is invoked when out of sync."""
    initial = {"name": "old"}
    exported = {"name": "new"}

    (tmp_project_dir / "environment.yml").write_text(yaml.dump(initial))
    export_mock.return_value = exported

    callback = MagicMock()
    pixi_sync_environment(tmp_project_dir, check=True, show_diff_callback=callback)

    callback.assert_called_once()
    args = callback.call_args[0]
    assert args[0] == initial
    assert args[1] == exported


class TestPixiSyncEnvironmentErrorHandling:
    """Tests for error handling."""

    def test_sync_raises_pixi_error(
        self, tmp_project_dir, sample_pixi_toml, export_mock
    ):
        """Test that PixiError is propagated."""
        export_mock.side_effect = PixiError("pixi failed")

        with pytest.raises(PixiError, match="pixi failed"):
            pixi_sync_environment(tmp_project_dir)

    def test_sync_raises_value_error(self, tmp_project_dir):
        """Test that ValueError is propagated when no manifest found."""
        # Don't create pixi.toml, creating a situation where manifest is missing
        with pytest.raises(ValueError, match="Could not find manifest"):
            pixi_sync_environment(tmp_project_dir)


class TestPixiSyncEnvironmentOptions:
    """Tests for various configuration options."""

    def test_sync_passes_options_to_export(
        self, tmp_project_dir, sample_pixi_toml, export_mock
    ):
        """Test that options are passed to export_conda_environment."""
        export_mock.return_value = {"name": "test"}

        pixi_sync_environment(
            tmp_project_dir,
            environment="dev",
            name="myenv",
        )

        export_mock.assert_called_once()
        call_kwargs = export_mock.call_args[1]
        assert call_kwargs["environment"] == "dev"
        assert call_kwargs["name"] == "myenv"

    def test_sync_custom_environment_file(
        self, tmp_project_dir, sample_pixi_toml, export_mock
    ):
        """Test using a custom environment filename."""
        export_mock.return_value = {"name": "test"}
        custom_file = "custom.yml"

        pixi_sync_environment(tmp_project_dir, environment_file=custom_file)

        assert (tmp_project_dir / custom_file).exists()


def test_sync_idempotent(tmp_project_dir, sample_pixi_toml, export_mock):
    """Test that running sync twice produces consistent results."""
    export_mock.return_value = {"name": "test", "dependencies": ["python"]}

    # First run: creates file
    result1 = pixi_sync_environment(tmp_project_dir)
    assert result1 is True

    # Second run: no change, still True
    result2 = pixi_sync_environment(tmp_project_dir)
    assert result2 is True

    assert (tmp_project_dir / "environment.yml").exists()
