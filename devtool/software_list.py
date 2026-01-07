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


@dataclass(frozen=True)
class LocalPackage:
    name: str
    version: str
    dir_path: str
    type: Literal["local"] = "local"

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipPackage:
    name: str
    version: str
    type: Literal["pip"] = "pip"

    def asdict(self) -> dict[str, Any]:
        return asdict(self)


type Package = GoPackage | RPMPackage | LocalPackage | PipPackage


def list_packages(project_root: Path) -> list[Package]:
    return (
        list_go_tools(project_root)
        + list_go_submodules(project_root)
        + list_rpms(project_root)
        + list_pip_packages(project_root)
        + list_local_tools(project_root)
    )


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


# RPMs that are installed only for building (e.g. compiling C extensions)
# and removed afterwards. These should not appear in Installed-Software.md.
_BUILD_ONLY_RPMS = {"gcc", "python3-devel", "python3-pip"}


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
        if package_name in _BUILD_ONLY_RPMS:
            continue
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


def list_local_tools(project_root: Path) -> list[LocalPackage]:
    local_tools: list[LocalPackage] = []
    version_re = re.compile(r"^VERSION=['\"]?(\d+\.\d+(\.\d+)?)['\"]?", re.MULTILINE)

    for local_tool_dir in sorted(project_root.joinpath("local-tools").iterdir()):
        if not local_tool_dir.is_dir():
            continue

        script = local_tool_dir / f"{local_tool_dir.name}.sh"
        if not script.exists():
            raise ValueError(
                f"Expected {script.name} to exist in {local_tool_dir.relative_to(project_root)}"
            )

        content = script.read_text()
        match = version_re.search(content)

        if not match:
            raise ValueError(
                f"Did not find VERSION line in {script.relative_to(project_root)} "
                "(must be in the form ^VERSION=x.y[.z], optionally with quotes)"
            )

        name = local_tool_dir.name
        version = match.group(1)

        local_tools.append(
            LocalPackage(
                name=name,
                version=version,
                dir_path=local_tool_dir.relative_to(project_root).as_posix(),
            )
        )

    return local_tools


def list_pip_packages(project_root: Path) -> list[PipPackage]:
    """List pip packages by reading names from requirements.in and versions from requirements.txt.

    Similar to how RPMs are handled with rpms.in.yaml (package names) and rpms.lock.yaml (versions).
    """
    pip_dir = project_root / "deps" / "pip"
    requirements_in = pip_dir / "requirements.in"
    requirements_txt = pip_dir / "requirements.txt"

    if not requirements_in.exists():
        return []

    # Parse package names from requirements.in (direct dependencies)
    package_names: list[str] = []
    for line in requirements_in.read_text().splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
        # Strip inline comments
        if " #" in line:
            line = line.split(" #")[0].strip()
        # Package names can have version specifiers, but we only want the name
        # Handle cases like "awscli" or "awscli>=1.0"
        package_name = re.split(r"[<>=!]", line)[0].strip()
        if package_name:
            package_names.append(package_name.lower())

    if not package_names:
        return []

    # Parse resolved versions from requirements.txt
    resolved_versions: dict[str, str] = {}
    for line in requirements_txt.read_text().splitlines():
        line = line.strip()
        # Skip empty lines, comments, and indented lines (dependency annotations)
        if not line or line.startswith("#") or line.startswith(" "):
            continue
        # Strip inline comments
        if " #" in line:
            line = line.split(" #")[0].strip()
        # Parse package==version format
        if "==" in line:
            name, version = line.split("==", 1)
            version = version.rstrip(" \\")
            resolved_versions[name.strip().lower()] = version.strip()

    # Match package names from requirements.in with versions from requirements.txt
    pip_packages: list[PipPackage] = []
    for package_name in package_names:
        version = resolved_versions.get(package_name)
        if version is None:
            raise ValueError(
                f"Package {package_name!r} from requirements.in not found in requirements.txt. "
                "Please regenerate requirements.txt with: uv pip compile --generate-hashes requirements.in -o requirements.txt"
            )
        pip_packages.append(PipPackage(name=package_name, version=version))

    return pip_packages
