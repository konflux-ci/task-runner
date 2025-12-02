from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, NotRequired, TypedDict

import yaml


@dataclass(frozen=True)
class GoPackage:
    name: str
    module_path: str
    version: str
    type: Literal["go-tool", "go-submodule"]

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RPMPackage:
    name: str
    version: str
    type: Literal["rpm"] = "rpm"

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


type Package = GoPackage | RPMPackage


def list_packages(project_root: Path) -> list[Package]:
    return list_go_tools(project_root) + list_go_submodules(project_root) + list_rpms(project_root)


class _GoMod(TypedDict):
    Tool: list[_GoModTool]
    Require: list[_GoModModule]


class _GoModTool(TypedDict):
    Path: str


class _GoModModule(TypedDict):
    Path: str
    Version: str


def list_go_tools(project_root: Path) -> list[GoPackage]:
    packages: list[GoPackage] = []
    for path in sorted(project_root.joinpath("deps/go-tools").iterdir()):
        if path.is_dir():
            packages.extend(_list_go_tools(path))
    return packages


def _list_go_tools(tool_dir: Path) -> Iterable[GoPackage]:
    proc = subprocess.run(
        ["go", "mod", "edit", "-json"],
        stdout=subprocess.PIPE,
        check=True,
        cwd=tool_dir,
    )
    go_mod: _GoMod = json.loads(proc.stdout)

    def find_parent_module(package_path: str) -> _GoModModule | None:
        for module in go_mod["Require"]:
            module_path = module["Path"]
            if package_path == module_path or package_path.startswith(f"{module_path}/"):
                return module
        return None

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

        yield GoPackage(
            name=name,
            module_path=module["Path"],
            version=module["Version"].removeprefix("v"),
            type="go-tool",
        )


def list_go_submodules(project_root: Path) -> list[GoPackage]:
    packages: list[GoPackage] = []

    for path in sorted(project_root.joinpath("deps/go-submodules").iterdir()):
        if not path.is_dir():
            continue

        name = path.name
        if name == "kubernetes":
            # We only install kubectl from the kubernetes repo
            name = "kubectl"

        tags = _list_local_tags(path) or _fetch_remote_tags(path)

        relpath = path.relative_to(project_root)
        if not tags:
            raise ValueError(
                f"The HEAD of the submodule at {relpath} doesn't have a tag! "
                "Please checkout to a semver tag."
            )

        try:
            version_match = next(
                match for tag in tags if (match := re.search(r"\d+\.\d+\.\d+", tag))
            )
        except StopIteration:
            raise ValueError(
                f"None of the tags for the submodule at {relpath} match semver. "
                f"Tags: {' '.join(tags)}"
            )

        module_path = f"./{path.relative_to(project_root).as_posix()}"
        packages.append(
            GoPackage(
                name=name,
                module_path=module_path,
                version=version_match.group(),
                type="go-submodule",
            )
        )

    return packages


def _list_local_tags(submodule_path: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "tag", "--points-at=HEAD"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
        cwd=submodule_path,
    )
    return proc.stdout.splitlines()


def _fetch_remote_tags(submodule_path: Path) -> list[str]:
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
        cwd=submodule_path,
    ).stdout.strip()

    remote_tags = subprocess.run(
        ["git", "ls-remote", "--tags", "origin"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
        cwd=submodule_path,
    ).stdout.splitlines()

    matching_tags: list[str] = []
    for tag_line in remote_tags:
        sha, tag = tag_line.split()
        tag = tag.removesuffix("^{}")
        if sha == head_sha:
            subprocess.run(
                ["git", "fetch", "origin", f"{tag}:{tag}"],
                cwd=submodule_path,
            )
            matching_tags.append(tag.removeprefix("refs/tags/"))

    return matching_tags


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


def list_rpms(project_root: Path) -> list[RPMPackage]:
    rpms_dir = project_root / "deps" / "rpm"

    rpms_in: _RpmsIn = yaml.safe_load((rpms_dir / "rpms.in.yaml").read_text())
    rpms_lock: _RpmsLock = yaml.safe_load((rpms_dir / "rpms.lock.yaml").read_text())

    packages: list[RPMPackage] = []
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
        packages.append(RPMPackage(name=package_name, version=version))

    return packages
