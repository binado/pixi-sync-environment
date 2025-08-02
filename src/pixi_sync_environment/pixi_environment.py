import json
import logging
import subprocess
from pathlib import Path
from typing import Iterable

from pixi_sync_environment.package_info import PackageInfo

logger = logging.getLogger(__name__)


def get_pixi_packages(manifest_path: Path, explicit: bool = False) -> list[PackageInfo]:
    logger.info("Getting explicit packages from pixi")
    args = ["pixi", "list", "--manifest-path", str(manifest_path), "--json"]
    if explicit:
        args.append("--explicit")
    cmd = " ".join(args)
    logger.info("Running %s", cmd)
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        logger.error(err.output)
        logger.exception(err)
        raise err

    package_list = json.loads(result.stdout)
    return [PackageInfo(**package) for package in package_list]


def create_environment_dict_from_packages(
    packages: Iterable[PackageInfo],
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
) -> dict:
    conda_packages = [package for package in packages if package.is_conda_package]
    pypi_packages = [package for package in packages if package.is_pypi_package]
    dependecies: list[str | dict] = [
        package.get_package_spec_str(include_build=include_build)
        for package in conda_packages
    ]
    if pypi_packages and include_pip_packages:
        pypi_package_specs = [
            package.get_package_spec_str(include_build=False)
            for package in pypi_packages
        ]
        dependecies.append({"pip": pypi_package_specs})
    environment_dict = {}
    if name is not None:
        environment_dict["name"] = name
    if prefix is not None:
        environment_dict["prefix"] = prefix
    if include_conda_channels:
        environment_dict["channels"] = list(
            {package.source for package in conda_packages}
        )
    environment_dict["dependencies"] = dependecies
    return environment_dict


def create_environment_dict_from_pixi(
    manifest_path: Path,
    explicit: bool = False,
    name: str | None = None,
    prefix: str | None = None,
    include_pip_packages: bool = False,
    include_conda_channels: bool = True,
    include_build: bool = False,
) -> dict:
    packages = get_pixi_packages(manifest_path, explicit=explicit)
    return create_environment_dict_from_packages(
        packages,
        name=name,
        prefix=prefix,
        include_pip_packages=include_pip_packages,
        include_conda_channels=include_conda_channels,
        include_build=include_build,
    )
