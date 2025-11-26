from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

import yaml


@dataclass(frozen=True)
class Package:
    name: str
    version: str
    installed_with: Literal["go", "rpm"]

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


class _GoMod(TypedDict):
    Tool: list[_GoModTool]
    Require: list[_GoModModule]


class _GoModTool(TypedDict):
    Path: str


class _GoModModule(TypedDict):
    Path: str
    Version: str


def list_go_packages(project_root: Path) -> list[Package]:
    proc = subprocess.run(
        ["go", "mod", "edit", "-json"],
        stdout=subprocess.PIPE,
        check=True,
        cwd=project_root / "deps" / "golang",
    )
    go_mod: _GoMod = json.loads(proc.stdout)

    def find_parent_module(package_path: str) -> _GoModModule | None:
        for module in go_mod["Require"]:
            module_path = module["Path"]
            if package_path == module_path or package_path.startswith(f"{module_path}/"):
                return module
        return None

    packages: list[Package] = []

    for tool in go_mod["Tool"]:
        package_path = tool["Path"]
        module = find_parent_module(package_path)
        if not module:
            raise ValueError(f"{package_path} has no parent module in go.mod")

        parts = package_path.split("/")
        if re.fullmatch(r"v\d+", parts[-1]):
            name = parts[-2]
        else:
            name = parts[-1]

        packages.append(
            Package(
                name=name,
                version=module["Version"].removeprefix("v"),
                installed_with="go",
            )
        )

    return packages


class _RpmsIn(TypedDict):
    packages: NotRequired[list[str]]
    reinstallPackages: NotRequired[list[str]]
    updatePackages: NotRequired[list[str]]
    arches: list[str]


class _RpmsLock(TypedDict):
    arches: list[_RpmsLockArch]


class _RpmsLockArch(TypedDict):
    arch: str
    packages: list[_RpmsLockPackage]


class _RpmsLockPackage(TypedDict):
    name: str
    evr: str


def list_rpms(project_root: Path) -> list[Package]:
    rpms_dir = project_root / "deps" / "rpm"

    rpms_in: _RpmsIn = yaml.safe_load((rpms_dir / "rpms.in.yaml").read_text())
    rpms_lock: _RpmsLock = yaml.safe_load((rpms_dir / "rpms.lock.yaml").read_text())

    packages: list[Package] = []
    package_names = (
        rpms_in.get("packages", [])
        + rpms_in.get("reinstallPackages", [])
        + rpms_in.get("updatePackages", [])
    )

    for package_name in package_names:
        evrs: dict[str, str | None] = {}
        for arch in rpms_lock["arches"]:
            try:
                resolved_package = next(p for p in arch["packages"] if p["name"] == package_name)
                evr = resolved_package["evr"]
            except StopIteration:
                evr = None

            evrs[arch["arch"]] = evr

        match list(set(evrs.values())):
            case [evr] if evr is not None:
                pass
            case _:
                raise ValueError(f"Mismatched or missing versions for {package_name} RPM: {evrs}")

        _, _, version = evr.rpartition(":")  # drop the epoch, if any
        packages.append(Package(name=package_name, version=version, installed_with="rpm"))

    return packages
