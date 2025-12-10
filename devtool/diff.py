import enum
import subprocess
from pathlib import Path
from typing import NamedTuple

from devtool.markdown import parse_package_table
from devtool.software_list import list_packages
from devtool.version import Version


class ChangeType(enum.IntEnum):
    """Change types in order of importance."""

    REMOVED = 4
    MAJOR = 3
    ADDED = 2
    MINOR = 1
    OTHER = 0

    def is_breaking(self) -> bool:
        return self >= ChangeType.MAJOR

    def is_feature(self) -> bool:
        return self >= ChangeType.MINOR


class ChangedPackage(NamedTuple):
    name: str
    old_version: str | None
    new_version: str | None

    def what_changed(self) -> ChangeType:
        if self.new_version is None:
            return ChangeType.REMOVED
        if self.old_version is None:
            return ChangeType.ADDED

        old_version = Version.parse(self.old_version)
        new_version = Version.parse(self.new_version)

        if old_version.major != new_version.major:
            return ChangeType.MAJOR
        if old_version.minor != new_version.minor:
            return ChangeType.MINOR

        # The patch number, the 4th version number for some RPMs, the release number...
        return ChangeType.OTHER


def diff_software(
    repo_root: Path, base_ref: str, head_ref: str | None = None
) -> list[ChangedPackage]:
    def git_show(ref: str, filepath: str) -> str:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{filepath}"],
            stdout=subprocess.PIPE,
            text=True,
            cwd=repo_root,
        )
        proc.check_returncode()
        return proc.stdout

    _fetch_version_tag_if_needed(repo_root, base_ref)
    old_versions = parse_package_table(git_show(base_ref, "Installed-Software.md"))
    if head_ref:
        _fetch_version_tag_if_needed(repo_root, head_ref)
        new_versions = parse_package_table(git_show(head_ref, "Installed-Software.md"))
    else:
        new_versions = {pkg.name: pkg.version for pkg in list_packages(repo_root)}

    changed_packages: list[ChangedPackage] = []

    for pkg_name in old_versions.keys() | new_versions.keys():
        old_version = old_versions.get(pkg_name)
        new_version = new_versions.get(pkg_name)
        if old_version != new_version:
            changed_packages.append(ChangedPackage(pkg_name, old_version, new_version))

    changed_packages.sort(key=lambda pkg: pkg.name)
    return changed_packages


def _fetch_version_tag_if_needed(repo_root: Path, ref: str) -> None:
    try:
        Version.parse(ref.removeprefix("v"))
    except ValueError:
        # ref is not a version tag
        return

    proc = subprocess.run(
        ["git", "rev-parse", ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=repo_root,
    )
    if proc.returncode == 0:
        # already have the tag
        return

    upstream = _find_upstream_remote(repo_root)
    if upstream is None:
        raise RuntimeError(
            "No remote found for konflux-ci/task-runner. "
            "Run 'git remote add upstream https://github.com/konflux-ci/task-runner.git'"
        )

    subprocess.run(
        ["git", "fetch", upstream, f"refs/tags/{ref}:refs/tags/{ref}"],
        cwd=repo_root,
        check=True,
    )


def _find_upstream_remote(repo_root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "remote", "-v"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    for line in proc.stdout.splitlines():
        name, repo, *_ = line.split()
        if "konflux-ci/task-runner" in repo:
            return name

    return None
