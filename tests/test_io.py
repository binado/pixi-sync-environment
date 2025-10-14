"""Tests for the io module."""

import pytest
import yaml

from pixi_sync_environment.io import (
    CONFIG_FILENAMES,
    MANIFEST_FILENAMES,
    find_project_dir,
    get_manifest_path,
    load_environment_file,
    save_environment_file,
)


class TestFindProjectDir:
    """Tests for find_project_dir function."""

    def test_find_project_dir_single_file(self, tmp_project_dir):
        """Test extracting directory from a single file."""
        pixi_file = tmp_project_dir / "pixi.toml"
        pixi_file.touch()

        result = find_project_dir([pixi_file])

        assert len(result) == 1
        assert result[0] == tmp_project_dir

    def test_find_project_dir_multiple_files_same_dir(self, tmp_project_dir):
        """Test deduplication when multiple files are in same directory."""
        pixi_file = tmp_project_dir / "pixi.toml"
        env_file = tmp_project_dir / "environment.yml"
        pixi_file.touch()
        env_file.touch()

        result = find_project_dir([pixi_file, env_file])

        assert len(result) == 1
        assert result[0] == tmp_project_dir

    def test_find_project_dir_multiple_directories(self, tmp_path):
        """Test handling multiple different project directories."""
        dir1 = tmp_path / "project1"
        dir2 = tmp_path / "project2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "pixi.toml"
        file2 = dir2 / "pyproject.toml"
        file1.touch()
        file2.touch()

        result = find_project_dir([file1, file2])

        assert len(result) == 2
        assert dir1 in result
        assert dir2 in result

    def test_find_project_dir_invalid_filename(self, tmp_project_dir):
        """Test that non-config files raise ValueError."""
        invalid_file = tmp_project_dir / "invalid.txt"
        invalid_file.touch()

        with pytest.raises(ValueError, match="Expected filename to be one of"):
            find_project_dir([invalid_file])

    def test_find_project_dir_all_config_types(self, tmp_project_dir):
        """Test that all CONFIG_FILENAMES are accepted."""
        files = []
        for filename in CONFIG_FILENAMES:
            file_path = tmp_project_dir / filename
            file_path.touch()
            files.append(file_path)

        result = find_project_dir(files)

        assert len(result) == 1
        assert result[0] == tmp_project_dir

    def test_find_project_dir_empty_list(self):
        """Test that empty input returns empty list."""
        result = find_project_dir([])

        assert result == []


class TestGetManifestPath:
    """Tests for get_manifest_path function."""

    def test_get_manifest_path_finds_pixi_toml(self, tmp_project_dir):
        """Test that pixi.toml is preferred when it exists."""
        pixi_file = tmp_project_dir / "pixi.toml"
        pixi_file.touch()

        result = get_manifest_path(tmp_project_dir)

        assert result == pixi_file

    def test_get_manifest_path_finds_both_prefers_pixi(self, tmp_project_dir):
        """Test that pixi.toml is preferred over pyproject.toml."""
        pixi_file = tmp_project_dir / "pixi.toml"
        pyproject_file = tmp_project_dir / "pyproject.toml"
        pixi_file.touch()
        pyproject_file.touch()

        result = get_manifest_path(tmp_project_dir)

        assert result == pixi_file

    def test_get_manifest_path_falls_back_to_pyproject(self, tmp_project_dir):
        """Test fallback to pyproject.toml when pixi.toml doesn't exist."""
        pyproject_file = tmp_project_dir / "pyproject.toml"
        pyproject_file.touch()

        result = get_manifest_path(tmp_project_dir)

        assert result == pyproject_file

    def test_get_manifest_path_raises_when_none(self, tmp_project_dir):
        """Test that ValueError is raised when no manifest exists."""
        with pytest.raises(ValueError, match="Could not find manifest path"):
            get_manifest_path(tmp_project_dir)

    def test_get_manifest_path_ignores_directories(self, tmp_project_dir):
        """Test that directories with manifest names are ignored."""
        # Create a directory named pixi.toml (not a file)
        pixi_dir = tmp_project_dir / "pixi.toml"
        pixi_dir.mkdir()

        with pytest.raises(ValueError, match="Could not find manifest path"):
            get_manifest_path(tmp_project_dir)

    def test_get_manifest_path_follows_precedence(self, tmp_project_dir):
        """Test that MANIFEST_FILENAMES order is respected."""
        # This verifies the implementation follows MANIFEST_FILENAMES order
        assert MANIFEST_FILENAMES == ("pixi.toml", "pyproject.toml")

        # Create only the second file
        pyproject_file = tmp_project_dir / MANIFEST_FILENAMES[1]
        pyproject_file.touch()

        result = get_manifest_path(tmp_project_dir)
        assert result == pyproject_file


class TestLoadEnvironmentFile:
    """Tests for load_environment_file function."""

    def test_load_environment_file_success(self, tmp_project_dir):
        """Test loading a valid YAML environment file."""
        env_file = tmp_project_dir / "environment.yml"
        env_data = {
            "name": "test-env",
            "channels": ["conda-forge"],
            "dependencies": ["python=3.10", "numpy=1.24"],
        }
        env_file.write_text(yaml.dump(env_data))

        result = load_environment_file(tmp_project_dir, "environment.yml")

        assert result == env_data
        assert result["name"] == "test-env"
        assert len(result["dependencies"]) == 2

    def test_load_environment_file_missing_with_raise(self, tmp_project_dir):
        """Test that FileNotFoundError is raised with raise_exception=True."""
        with pytest.raises(FileNotFoundError):
            load_environment_file(
                tmp_project_dir, "nonexistent.yml", raise_exception=True
            )

    def test_load_environment_file_missing_no_raise(self, tmp_project_dir):
        """Test that None is returned with raise_exception=False."""
        result = load_environment_file(
            tmp_project_dir, "nonexistent.yml", raise_exception=False
        )

        assert result is None

    def test_load_environment_file_invalid_yaml(self, tmp_project_dir):
        """Test that malformed YAML raises YAMLError."""
        env_file = tmp_project_dir / "bad.yml"
        env_file.write_text("{ invalid: yaml: structure::")

        with pytest.raises(yaml.YAMLError):
            load_environment_file(tmp_project_dir, "bad.yml")

    def test_load_environment_file_empty(self, tmp_project_dir):
        """Test loading an empty YAML file returns None."""
        env_file = tmp_project_dir / "empty.yml"
        env_file.write_text("")

        result = load_environment_file(tmp_project_dir, "empty.yml")

        assert result is None

    def test_load_environment_file_custom_name(self, tmp_project_dir):
        """Test loading with a custom filename."""
        custom_file = tmp_project_dir / "custom-env.yml"
        env_data = {"name": "custom"}
        custom_file.write_text(yaml.dump(env_data))

        result = load_environment_file(tmp_project_dir, "custom-env.yml")

        assert result["name"] == "custom"

    def test_load_environment_file_with_list(self, tmp_project_dir):
        """Test that YAML files returning lists are handled."""
        env_file = tmp_project_dir / "list.yml"
        env_file.write_text("- item1\n- item2\n- item3")

        result = load_environment_file(tmp_project_dir, "list.yml")

        assert isinstance(result, list)
        assert len(result) == 3


class TestSaveEnvironmentFile:
    """Tests for save_environment_file function."""

    def test_save_environment_file_creates_file(self, tmp_project_dir):
        """Test that save creates a new file."""
        env_data = {
            "name": "test-env",
            "channels": ["conda-forge"],
            "dependencies": ["python=3.10"],
        }

        save_environment_file(env_data, tmp_project_dir, "environment.yml")

        env_file = tmp_project_dir / "environment.yml"
        assert env_file.exists()
        assert env_file.is_file()

    def test_save_environment_file_valid_yaml(self, tmp_project_dir):
        """Test that saved file contains valid YAML."""
        env_data = {
            "name": "test-env",
            "channels": ["conda-forge"],
            "dependencies": ["python=3.10"],
        }

        save_environment_file(env_data, tmp_project_dir, "environment.yml")

        # Load it back to verify it's valid YAML
        result = load_environment_file(tmp_project_dir, "environment.yml")
        assert result == env_data

    def test_save_environment_file_preserves_structure(self, tmp_project_dir):
        """Test round-trip: save and load preserves structure."""
        env_data = {
            "name": "complex-env",
            "channels": ["conda-forge", "defaults"],
            "dependencies": [
                "python=3.10",
                "numpy=1.24",
                {"pip": ["requests==2.31.0", "pytest>=7.0"]},
            ],
        }

        save_environment_file(env_data, tmp_project_dir, "environment.yml")
        result = load_environment_file(tmp_project_dir, "environment.yml")

        assert result == env_data
        assert result["name"] == "complex-env"
        assert len(result["channels"]) == 2
        assert isinstance(result["dependencies"][2], dict)
        assert "pip" in result["dependencies"][2]

    def test_save_environment_file_formatting(self, tmp_project_dir):
        """Test that YAML is formatted correctly (block style)."""
        env_data = {
            "name": "test-env",
            "dependencies": ["python=3.10", "numpy=1.24"],
        }

        save_environment_file(env_data, tmp_project_dir, "environment.yml")

        # Read raw content
        env_file = tmp_project_dir / "environment.yml"
        content = env_file.read_text()

        # Block style means no inline brackets/braces
        assert "[" not in content
        assert "{" not in content
        # Should have proper indentation
        assert "name: test-env" in content
        assert "- python=3.10" in content

    def test_save_environment_file_overwrites_existing(self, tmp_project_dir):
        """Test that save overwrites existing file."""
        env_file = tmp_project_dir / "environment.yml"
        env_file.write_text("old content")

        new_data = {"name": "new-env"}
        save_environment_file(new_data, tmp_project_dir, "environment.yml")

        result = load_environment_file(tmp_project_dir, "environment.yml")
        assert result == new_data
        assert result["name"] == "new-env"

    def test_save_environment_file_custom_name(self, tmp_project_dir):
        """Test saving with a custom filename."""
        env_data = {"name": "custom"}

        save_environment_file(env_data, tmp_project_dir, "custom-env.yml")

        custom_file = tmp_project_dir / "custom-env.yml"
        assert custom_file.exists()

        result = load_environment_file(tmp_project_dir, "custom-env.yml")
        assert result["name"] == "custom"

    def test_save_environment_file_with_list(self, tmp_project_dir):
        """Test saving a list (though unusual for environment files)."""
        list_data = ["item1", "item2", "item3"]

        save_environment_file(list_data, tmp_project_dir, "list.yml")

        result = load_environment_file(tmp_project_dir, "list.yml")
        assert result == list_data

    def test_save_environment_file_preserves_order(self, tmp_project_dir):
        """Test that key order is preserved (sort_keys=False)."""
        # Use a dict with specific order
        env_data = {
            "name": "test",
            "prefix": "/path/to/env",
            "channels": ["conda-forge"],
            "dependencies": ["python"],
        }

        save_environment_file(env_data, tmp_project_dir, "environment.yml")

        # Read raw content and check order
        env_file = tmp_project_dir / "environment.yml"
        content = env_file.read_text()
        lines = content.split("\n")

        # Find line numbers
        name_line = next(i for i, line in enumerate(lines) if "name:" in line)
        prefix_line = next(i for i, line in enumerate(lines) if "prefix:" in line)
        channels_line = next(i for i, line in enumerate(lines) if "channels:" in line)
        deps_line = next(i for i, line in enumerate(lines) if "dependencies:" in line)

        # Verify order is preserved
        assert name_line < prefix_line < channels_line < deps_line
