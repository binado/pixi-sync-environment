from dataclasses import dataclass
from typing import Literal


@dataclass
class PackageInfo:
    name: str
    version: str
    size_bytes: int
    build: str | None
    kind: Literal["conda", "pypi"]
    source: str
    is_explicit: bool
    is_editable: bool | None = None

    @property
    def is_conda_package(self):
        return self.kind == "conda"

    @property
    def is_pypi_package(self):
        return self.kind == "pypi"

    def get_package_spec_str(self, include_build: bool = False) -> str:
        properties = [self.name, self.version]
        if include_build and self.build is not None:
            properties.append(self.build)
        return "=".join(properties)
