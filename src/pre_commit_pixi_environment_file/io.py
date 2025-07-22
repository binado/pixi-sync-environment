from pathlib import Path

import yaml


def find_project_dir(root_dir: str = ".") -> Path | None:
    """Find the directory containing the first pyproject.toml file encountered."""
    path = Path(root_dir)
    try:
        pyproject_file = next(path.rglob("pyproject.toml"))
        return pyproject_file.parent
    except StopIteration:
        return None


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
