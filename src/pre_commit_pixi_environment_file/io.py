from pathlib import Path

import yaml

CONFIG_FILENAMES = ["environment.yml", "pixi.toml", "pyproject.toml", "pixi.lock"]


def find_project_dir(input_file: Path) -> Path | None:
    filename = input_file.name
    if filename not in CONFIG_FILENAMES:
        raise ValueError(f"Expected filename to be one of {CONFIG_FILENAMES}")
    return input_file.parent


def load_environment_file(
    path_dir: Path,
    environment_file: str = "environment.yml",
    raise_exception: bool = True,
) -> dict | list | None:
    filepath = path_dir / environment_file
    try:
        with open(filepath) as file:
            return yaml.safe_load(file)
    except FileNotFoundError as err:
        if not raise_exception:
            return None
        raise err


def save_environment_file(
    data, path_dir: Path, environment_file: str = "environment.yml"
):
    filepath = path_dir / environment_file
    with open(filepath, mode="w") as file:
        yaml.dump(
            data,
            file,
            default_flow_style=False,
            allow_unicode=True,
            encoding="utf-8",
            indent=2,
            sort_keys=False,
        )
