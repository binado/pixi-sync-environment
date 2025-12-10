"""Integration tests for pixi-sync-environment CLI.

These tests use real subprocess calls and actual files to test the CLI behavior
in a realistic scenario, closely simulating how users would actually use the tool.
"""

import subprocess
import tempfile
from pathlib import Path

import yaml


class TestCLIIntegration:
    """Integration tests for the pixi_sync_environment CLI."""

    def test_cli_creates_environment_file(self, pixi_project_with_pypi):
        """Test that CLI creates environment.yml from pixi.toml."""
        # Run pixi_sync_environment
        subprocess.run(
            ["pixi_sync_environment", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Check that environment.yml was created
        env_file = pixi_project_with_pypi / "environment.yml"
        assert env_file.exists(), "environment.yml should be created"

        # Load and validate the generated file
        with open(env_file) as f:
            generated_env = yaml.safe_load(f)

        # Basic structure validation
        assert "name" in generated_env
        assert "channels" in generated_env
        assert "dependencies" in generated_env
        assert "conda-forge" in generated_env["channels"]

        # Check that key dependencies are present
        deps = generated_env["dependencies"]
        python_deps = [
            dep for dep in deps if isinstance(dep, str) and dep.startswith("python")
        ]
        assert len(python_deps) > 0, "Python dependency should be present"

        # Check for pip dependencies
        pip_deps = [dep for dep in deps if isinstance(dep, dict) and "pip" in dep]
        assert len(pip_deps) > 0, "pip dependencies should be present"

    def test_cli_check_mode_new_file(self, pixi_project_with_pypi):
        """Test check mode when environment.yml doesn't exist."""
        # Run in check mode
        result = subprocess.run(
            ["pixi_sync_environment", "--check", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
        )

        # Should exit with code 1 (out of sync)
        assert result.returncode == 1, (
            "Check mode should exit with code 1 when file doesn't exist"
        )
        assert "does not exist" in result.stderr or "does not exist" in result.stdout

    def test_cli_check_mode_in_sync(self, pixi_project_with_pypi):
        """Test check mode when files are in sync."""
        # Create environment.yml by running sync first
        subprocess.run(
            ["pixi_sync_environment", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Now run check mode
        result = subprocess.run(
            ["pixi_sync_environment", "--check", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
        )

        # Should exit with code 0 (in sync)
        assert result.returncode == 0, (
            f"Check mode should exit with code 0 when files are in sync. stderr: {result.stderr}"
        )

    def test_cli_with_custom_environment_name(self, pixi_project_with_pypi):
        """Test CLI with custom environment name."""
        # Run with custom name
        subprocess.run(
            ["pixi_sync_environment", "--name", "my-custom-env", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Check that environment.yml was created with custom name
        env_file = pixi_project_with_pypi / "environment.yml"
        with open(env_file) as f:
            generated_env = yaml.safe_load(f)

        assert generated_env["name"] == "my-custom-env", (
            "Custom environment name should be used"
        )

    def test_cli_with_custom_output_file(self, pixi_project_with_pypi):
        """Test CLI with custom output file name."""
        # Run with custom output file
        custom_file = "custom-environment.yml"
        subprocess.run(
            ["pixi_sync_environment", "--environment-file", custom_file, "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Check that custom file was created
        custom_env_file = pixi_project_with_pypi / custom_file
        assert custom_env_file.exists(), f"Custom file {custom_file} should be created"

    def test_cli_idempotency(self, pixi_project_with_pypi):
        """Test that running CLI twice produces the same result."""
        # Run first time
        subprocess.run(
            ["pixi_sync_environment", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Copy the first result
        env_file = pixi_project_with_pypi / "environment.yml"
        first_content = env_file.read_text()

        # Run second time
        subprocess.run(
            ["pixi_sync_environment", "pixi.toml"],
            cwd=pixi_project_with_pypi,
            capture_output=True,
            text=True,
            check=True,
        )

        # Content should be identical
        second_content = env_file.read_text()
        assert first_content == second_content, (
            "Running CLI twice should produce identical results"
        )

    def test_cli_with_real_pixi_project_structure(self):
        """Test with a more complex real-world pixi project structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)

            # Create a more complex pixi.toml
            pixi_toml = project_dir / "pixi.toml"
            pixi_toml.write_text("""
[workspace]
name = "complex-project"
version = "1.0.0"
channels = ["conda-forge", "bioconda"]
platforms = ["linux-64", "osx-64"]

[dependencies]
python = "3.11.*"
numpy = "1.24.*"
pandas = ">=1.5.0"
scipy = "*"
matplotlib = "*"

[pypi-dependencies]
requests = ">=2.28.0"
click = ">=8.0.0"

[feature.dev.dependencies]
pytest = "7.*"
black = "23.*"

[feature.dev.pypi-dependencies]
pytest-cov = ">=4.0.0"
""")

            # Run pixi_sync_environment
            subprocess.run(
                ["pixi_sync_environment", "pixi.toml"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            # Verify the output
            env_file = project_dir / "environment.yml"
            assert env_file.exists()

            with open(env_file) as f:
                generated_env = yaml.safe_load(f)

            # Check complex structure
            assert "channels" in generated_env
            assert "conda-forge" in generated_env["channels"]
            assert "dependencies" in generated_env

            # Check for specific packages
            deps = generated_env["dependencies"]
            dep_strings = [dep for dep in deps if isinstance(dep, str)]
            assert any("python" in dep for dep in dep_strings)
            assert any("numpy" in dep for dep in dep_strings)
