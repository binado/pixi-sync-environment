"""Pixi environment integration using native pixi workspace export.

This module provides functions for exporting pixi environments to conda
environment.yml format using pixi's built-in export functionality.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class PixiError(Exception):
    """Exception raised when pixi command operations fail.

    Attributes
    ----------
    message : str
        The error message.
    stdout : str, optional
        Standard output from the failed command.
    stderr : str, optional
        Standard error output from the failed command.
    """

    def __init__(self, message: str, stdout: str = "", stderr: str = ""):
        self.message = message
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(self.message)


def check_pixi_availability() -> None:
    """Check if pixi command is available and accessible.

    Raises
    ------
    PixiError
        If pixi command is not found or not executable.
    """
    if not shutil.which("pixi"):
        raise PixiError(
            "pixi command not found. Please install pixi first. "
            "Visit https://pixi.sh for installation instructions."
        )

    try:
        result = subprocess.run(
            ["pixi", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        logger.debug("Found pixi version: %s", result.stdout.strip())
    except subprocess.CalledProcessError as err:
        raise PixiError(
            f"pixi command is not working properly: {err.stderr}",
            stdout=err.stdout,
            stderr=err.stderr,
        ) from err
    except subprocess.TimeoutExpired as err:
        raise PixiError(
            "pixi command timed out - this may indicate an installation issue"
        ) from err
    except FileNotFoundError as err:
        raise PixiError("pixi command not found. Please install pixi first.") from err


def export_conda_environment(
    manifest_path: Path,
    environment: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Export a pixi environment to conda environment.yml format.

    Uses `pixi workspace export conda-environment` to generate the environment
    specification directly from pixi.

    Parameters
    ----------
    manifest_path : Path
        Path to the pixi manifest file (pixi.toml or pyproject.toml).
    environment : str or None, optional
        Name of the pixi environment to export. If None, uses the default
        environment. Default is None.
    name : str or None, optional
        Custom name to use for the exported conda environment.
        If None, pixi uses the environment name. Default is None.

    Returns
    -------
    dict
        Dictionary suitable for serializing to conda environment.yml format.
        Contains keys like 'name', 'channels', 'dependencies'.

    Raises
    ------
    PixiError
        If the pixi command fails or returns invalid output.
    FileNotFoundError
        If the manifest path does not exist.
    """
    check_pixi_availability()

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    logger.info(
        "Exporting conda environment from pixi environment '%s'",
        environment or "default",
    )

    # Use a temporary file instead of stdout due to pixi export issue
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".yml", delete=False
    ) as tmp_file:
        temp_path = tmp_file.name

    args = [
        "pixi",
        "workspace",
        "export",
        "conda-environment",
        "--manifest-path",
        str(manifest_path),
        temp_path,  # Output to temporary file
    ]

    if environment:
        args.extend(["--environment", environment])

    if name:
        args.extend(["--name", name])

    cmd = " ".join(args)
    logger.info("Running: %s", cmd)

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )

        # Read the exported environment from the temporary file
        try:
            with open(temp_path, "r") as f:
                result_stdout = f.read()
        except FileNotFoundError:
            raise PixiError(
                f"pixi export failed to create output file at {temp_path}",
                stdout=result.stdout,
                stderr=result.stderr,
            )
        finally:
            # Clean up the temporary file
            try:
                Path(temp_path).unlink()
            except FileNotFoundError:
                pass
    except subprocess.CalledProcessError as err:
        logger.error("pixi command failed with code %d", err.returncode)
        logger.error("stdout: %s", err.stdout)
        logger.error("stderr: %s", err.stderr)

        if "environment" in err.stderr.lower() and environment:
            raise PixiError(
                f"Environment '{environment}' not found in pixi manifest. "
                f"Available environments can be listed with 'pixi info'.",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err
        elif "manifest" in err.stderr.lower():
            raise PixiError(
                f"Invalid or corrupted pixi manifest at {manifest_path}",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err
        else:
            raise PixiError(
                f"pixi workspace export command failed: {err.stderr}",
                stdout=err.stdout,
                stderr=err.stderr,
            ) from err

    except subprocess.TimeoutExpired as err:
        raise PixiError(
            "pixi workspace export command timed out after 60 seconds. "
            "This may indicate a very large environment or network issues."
        ) from err

    try:
        environment_dict = yaml.safe_load(result_stdout)
        logger.info("Successfully exported conda environment from pixi")
        return environment_dict
    except yaml.YAMLError as err:
        logger.error("Invalid YAML output from pixi: %s", result_stdout[:200])
        raise PixiError(
            f"pixi command returned invalid YAML: {err}",
            stdout=result_stdout,
            stderr=result.stderr,
        ) from err
