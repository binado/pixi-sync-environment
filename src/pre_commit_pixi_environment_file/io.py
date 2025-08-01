from pathlib import Path

import yaml

MANIFEST_FILENAMES = ("pixi.toml", "pyproject.toml")
CONFIG_FILENAMES = (*MANIFEST_FILENAMES, "environment.yml", "pixi.lock")


def find_project_dir(input_files: list[Path]) -> list[Path]:
    path_dir = set()
    for input_file in input_files:
        filename = input_file.name
        if filename not in CONFIG_FILENAMES:
            raise ValueError(f"Expected filename to be one of {CONFIG_FILENAMES}")
        path_dir.add(input_file.parent)
    return list(path_dir)


def get_manifest_path(path_dir: Path) -> Path:
    for manifest_filename in MANIFEST_FILENAMES:
        manifest_path = path_dir / manifest_filename
        if manifest_path.is_file():
            return manifest_path

    raise ValueError(f"Could not find manifest path on directory {path_dir}")


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
