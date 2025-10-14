"""Tests for the CLI module."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from pixi_sync_environment.cli import _show_diff, get_parser, main
from pixi_sync_environment.pixi_environment import PixiError


class TestGetParser:
    """Tests for get_parser function."""

    def test_get_parser_returns_parser(self):
        """Test that get_parser returns an ArgumentParser."""
        parser = get_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parse_minimal_args(self):
        """Test parsing with just input files (minimal args)."""
        parser = get_parser()
        args = parser.parse_args(["pixi.toml"])

        assert len(args.input_files) == 1
        assert args.input_files[0] == Path("pixi.toml")
        assert args.environment_file == "environment.yml"
        assert args.explicit is False
        assert args.name is None
        assert args.prefix is None
        assert args.environment == "default"
        assert args.include_pip_packages is False
        assert args.include_conda_channels is True
        assert args.include_build is False
        assert args.check is False

    def test_parse_check_flag(self):
        """Test that --check flag is parsed correctly."""
        parser = get_parser()
        args = parser.parse_args(["--check", "pixi.toml"])

        assert args.check is True

    def test_parse_explicit_flag(self):
        """Test that --explicit flag is parsed correctly."""
        parser = get_parser()
        args = parser.parse_args(["--explicit", "pixi.toml"])

        assert args.explicit is True

    def test_parse_environment_file(self):
        """Test custom environment file name."""
        parser = get_parser()
        args = parser.parse_args(["--environment-file", "custom.yml", "pixi.toml"])

        assert args.environment_file == "custom.yml"

    def test_parse_name(self):
        """Test custom environment name."""
        parser = get_parser()
        args = parser.parse_args(["--name", "myenv", "pixi.toml"])

        assert args.name == "myenv"

    def test_parse_prefix(self):
        """Test custom environment prefix."""
        parser = get_parser()
        args = parser.parse_args(["--prefix", "/opt/env", "pixi.toml"])

        assert args.prefix == "/opt/env"

    def test_parse_environment(self):
        """Test custom pixi environment."""
        parser = get_parser()
        args = parser.parse_args(["--environment", "dev", "pixi.toml"])

        assert args.environment == "dev"

    def test_parse_include_pip_packages(self):
        """Test --include-pip-packages flag."""
        parser = get_parser()
        args = parser.parse_args(["--include-pip-packages", "pixi.toml"])

        assert args.include_pip_packages is True

    def test_parse_no_include_conda_channels(self):
        """Test --no-include-conda-channels flag."""
        parser = get_parser()
        args = parser.parse_args(["--no-include-conda-channels", "pixi.toml"])

        assert args.include_conda_channels is False

    def test_parse_include_build(self):
        """Test --include-build flag."""
        parser = get_parser()
        args = parser.parse_args(["--include-build", "pixi.toml"])

        assert args.include_build is True

    def test_parse_multiple_input_files(self):
        """Test parsing multiple input files."""
        parser = get_parser()
        args = parser.parse_args(["pixi.toml", "pyproject.toml", "environment.yml"])

        assert len(args.input_files) == 3
        assert args.input_files[0] == Path("pixi.toml")
        assert args.input_files[1] == Path("pyproject.toml")
        assert args.input_files[2] == Path("environment.yml")

    def test_parse_all_flags(self):
        """Test parsing with all flags set."""
        parser = get_parser()
        args = parser.parse_args(
            [
                "--check",
                "--explicit",
                "--environment-file",
                "custom.yml",
                "--name",
                "myenv",
                "--prefix",
                "/opt/env",
                "--environment",
                "dev",
                "--include-pip-packages",
                "--no-include-conda-channels",
                "--include-build",
                "pixi.toml",
            ]
        )

        assert args.check is True
        assert args.explicit is True
        assert args.environment_file == "custom.yml"
        assert args.name == "myenv"
        assert args.prefix == "/opt/env"
        assert args.environment == "dev"
        assert args.include_pip_packages is True
        assert args.include_conda_channels is False
        assert args.include_build is True


class TestShowDiff:
    """Tests for _show_diff function."""

    def test_show_diff_new_file(self, capsys):
        """Test diff output when file doesn't exist (current_dict is None)."""
        new_dict = {"name": "test", "dependencies": ["python"]}

        _show_diff(None, new_dict, "environment.yml")

        captured = capsys.readouterr()
        assert "New file content:" in captured.out
        assert "name: test" in captured.out
        assert "dependencies:" in captured.out

    def test_show_diff_differences(self, capsys):
        """Test diff output when files differ."""
        current_dict = {"name": "old", "dependencies": ["python=3.9"]}
        new_dict = {"name": "new", "dependencies": ["python=3.10"]}

        _show_diff(current_dict, new_dict, "environment.yml")

        captured = capsys.readouterr()
        assert "Differences in environment.yml:" in captured.out
        assert (
            "current environment.yml" in captured.out
            or "new environment.yml" in captured.out
        )
        # Should contain diff markers
        assert "-" in captured.out or "+" in captured.out

    def test_show_diff_no_output_when_same(self, capsys):
        """Test that no diff is shown when dicts are identical."""
        env_dict = {"name": "test", "dependencies": ["python"]}

        _show_diff(env_dict, env_dict, "environment.yml")

        captured = capsys.readouterr()
        # Should not output differences when they're the same
        assert "Differences" not in captured.out


class TestMain:
    """Tests for main function."""

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_successful_sync(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test successful sync workflow."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.return_value = True

        # Should complete without raising SystemExit on success
        try:
            main()
        except SystemExit as exc:
            # If it does exit, should be code 0
            assert exc.code is None or exc.code == 0

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_check_mode_in_sync(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test check mode when files are in sync."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pixi_sync_environment", "--check", str(tmp_project_dir / "pixi.toml")],
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.return_value = True  # Files in sync

        # Should complete without raising SystemExit on success
        try:
            main()
        except SystemExit as exc:
            # If it does exit, should be code 0
            assert exc.code is None or exc.code == 0

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_check_mode_out_of_sync(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test check mode when files are out of sync."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["pixi_sync_environment", "--check", str(tmp_project_dir / "pixi.toml")],
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.return_value = False  # Files out of sync

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_multiple_directories(
        self, mock_find_dirs, mock_sync, tmp_path, monkeypatch
    ):
        """Test processing multiple project directories."""
        dir1 = tmp_path / "proj1"
        dir2 = tmp_path / "proj2"
        dir1.mkdir()
        dir2.mkdir()

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pixi_sync_environment",
                str(dir1 / "pixi.toml"),
                str(dir2 / "pixi.toml"),
            ],
        )
        mock_find_dirs.return_value = [dir1, dir2]
        mock_sync.return_value = True

        # Should complete without raising SystemExit on success
        try:
            main()
        except SystemExit as exc:
            # If it does exit, should be code 0
            assert exc.code is None or exc.code == 0

        assert mock_sync.call_count == 2

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_partial_failure(
        self, mock_find_dirs, mock_sync, tmp_path, monkeypatch
    ):
        """Test that partial failure exits with code 1."""
        dir1 = tmp_path / "proj1"
        dir2 = tmp_path / "proj2"
        dir1.mkdir()
        dir2.mkdir()

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pixi_sync_environment",
                str(dir1 / "pixi.toml"),
                str(dir2 / "pixi.toml"),
            ],
        )
        mock_find_dirs.return_value = [dir1, dir2]
        # First succeeds, second raises error
        mock_sync.side_effect = [True, PixiError("test error")]

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_total_failure(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that total failure exits with code 1."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.side_effect = PixiError("test error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_invalid_input_files(self, mock_find_dirs, monkeypatch):
        """Test that invalid input files exit with code 1."""
        monkeypatch.setattr(sys, "argv", ["pixi_sync_environment", "invalid.txt"])
        mock_find_dirs.side_effect = ValueError("Invalid filename")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_no_project_dirs(self, mock_find_dirs, monkeypatch):
        """Test that no valid directories exits with code 1."""
        monkeypatch.setattr(sys, "argv", ["pixi_sync_environment", "pixi.toml"])
        mock_find_dirs.return_value = []

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_pixi_error(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that PixiError is caught and logged."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.side_effect = PixiError("pixi command failed")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_value_error(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that ValueError is caught and logged."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.side_effect = ValueError("No manifest found")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_keyboard_interrupt(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that KeyboardInterrupt is handled gracefully."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_unexpected_exception(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that unexpected exceptions are handled."""
        monkeypatch.setattr(
            sys, "argv", ["pixi_sync_environment", str(tmp_project_dir / "pixi.toml")]
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.side_effect = RuntimeError("Unexpected error")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("pixi_sync_environment.cli.pixi_sync_environment")
    @patch("pixi_sync_environment.cli.find_project_dir")
    def test_main_passes_all_arguments(
        self, mock_find_dirs, mock_sync, tmp_project_dir, monkeypatch
    ):
        """Test that all CLI arguments are passed to pixi_sync_environment."""
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "pixi_sync_environment",
                "--check",
                "--explicit",
                "--environment-file",
                "custom.yml",
                "--name",
                "myenv",
                "--prefix",
                "/opt/env",
                "--environment",
                "dev",
                "--include-pip-packages",
                "--no-include-conda-channels",
                "--include-build",
                str(tmp_project_dir / "pixi.toml"),
            ],
        )
        mock_find_dirs.return_value = [tmp_project_dir]
        mock_sync.return_value = True

        # Should complete without raising SystemExit on success
        try:
            main()
        except SystemExit as exc:
            # If it does exit, should be code 0
            assert exc.code is None or exc.code == 0

        # Verify all arguments were passed
        call_kwargs = mock_sync.call_args[1]
        assert call_kwargs["environment"] == "dev"
        assert call_kwargs["environment_file"] == "custom.yml"
        assert call_kwargs["explicit"] is True
        assert call_kwargs["name"] == "myenv"
        assert call_kwargs["prefix"] == "/opt/env"
        assert call_kwargs["include_pip_packages"] is True
        assert call_kwargs["include_conda_channels"] is False
        assert call_kwargs["include_build"] is True
        assert call_kwargs["check"] is True
