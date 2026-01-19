import json
import platform
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest

from tests.utils.container import Container


@pytest.fixture(scope="module")
def context_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    contextdir = tmp_path_factory.mktemp("buildcontext")
    # We're going to mount this directory into the container image, which runs as
    # a non-root user. Allow that user to read this directory.
    contextdir.chmod(0o777)

    base_image = "registry.access.redhat.com/ubi10/ubi-micro@sha256:2946fa1b951addbcd548ef59193dc0af9b3e9fedb0287b4ddb6e697b06581622"

    # Pre-pull the base image and make it available as an oci archive in the context directory
    # (so that each test doesn't have to re-pull the base image; this speeds up tests)
    subprocess.run(
        [
            "skopeo",
            "copy",
            # For the Mac users out there (they *can* build from a linux image,
            # but we have to explicitly tell skopeo to not try to pull a macos image)
            "--override-os=linux",
            "--remove-signatures",
            f"docker://{base_image}",
            f"oci:{contextdir / 'base_image'}",
        ],
        check=True,
    )

    contextdir.joinpath("Containerfile").write_text(
        dedent(
            """
            FROM oci:./base_image
            RUN touch /tmp/foo.txt
            """
        )
    )
    return contextdir


def test_buildah_uses_native_overlay(task_runner_container: Container) -> None:
    proc = task_runner_container.run_cmd(
        ["buildah", "info", "--log-level=debug"],
        volumes=["/home/taskuser/.local/share/containers"],
    )
    info = json.loads(proc.stdout)

    assert info["store"]["GraphDriverName"] == "overlay"
    assert info["store"]["GraphStatus"]["Native Overlay Diff"] == "true"

    assert "overlay: test mount with multiple lowers succeeded" in proc.stderr
    assert "Unable to create kernel-style whiteout: operation not permitted" not in proc.stderr


@pytest.mark.xfail(reason="https://github.com/containers/buildah/issues/6640")
def test_buildah_uses_native_overlay_as_root(task_runner_container: Container) -> None:
    proc = task_runner_container.run_cmd(
        ["buildah", "info", "--log-level=debug"],
        volumes=["/var/lib/containers"],
        user="0",
    )
    info = json.loads(proc.stdout)

    assert info["store"]["GraphDriverName"] == "overlay"
    assert info["store"]["GraphStatus"]["Native Overlay Diff"] == "true"

    assert "overlay: test mount with multiple lowers succeeded" in proc.stderr
    assert "Unable to create kernel-style whiteout: operation not permitted" not in proc.stderr


@pytest.mark.parametrize("user", ["taskuser", "root"])
@pytest.mark.skipif(
    platform.system() == "Darwin",
    reason="Claims to somehow use the native overlay even without the volume mount",
)
def test_buildah_falls_back_to_fuse_overlayfs(user: str, task_runner_container: Container) -> None:
    proc = task_runner_container.run_cmd(
        ["buildah", "info", "--log-level=debug"],
        # Not mounting a volume over container storage directory => native overlay not usable
        devices=["/dev/fuse"],
        user=user,
    )
    info = json.loads(proc.stdout)

    assert info["store"]["GraphDriverName"] == "overlay"
    assert info["store"]["GraphStatus"]["Native Overlay Diff"] == "false"

    assert "Unable to create kernel-style whiteout: operation not permitted" in proc.stderr


@pytest.mark.parametrize(
    "use_native_overlay",
    [pytest.param(True, id="native_overlay"), pytest.param(False, id="fuse_overlayfs")],
)
def test_buildah_build_works(
    use_native_overlay: bool, task_runner_container: Container, context_dir: Path
) -> None:
    volumes = [f"{context_dir}:{context_dir}"]
    devices = []
    if use_native_overlay:
        volumes.append("/home/taskuser/.local/share/containers")
    else:
        devices.append("/dev/fuse")

    task_runner_container.run_cmd(
        ["buildah", "build", "."],
        volumes=volumes,
        devices=devices,
        workdir=context_dir,
        cap_drop=["ALL"],
        cap_add=["SETUID", "SETGID", "SYS_CHROOT"],
    )


@pytest.mark.parametrize(
    "use_native_overlay",
    [pytest.param(True, id="native_overlay"), pytest.param(False, id="fuse_overlayfs")],
)
def test_buildah_build_works_as_root(
    use_native_overlay: bool, task_runner_container: Container, context_dir: Path
) -> None:
    volumes = [f"{context_dir}:{context_dir}"]
    devices = []
    if use_native_overlay:
        volumes.append("/var/lib/containers")
    else:
        devices.append("/dev/fuse")

    task_runner_container.run_cmd(
        ["buildah", "build", "--log-level=debug", "."],
        volumes=volumes,
        devices=devices,
        workdir=context_dir,
        cap_drop=["ALL"],
        cap_add=["SETUID", "SETGID", "SYS_CHROOT", "SETFCAP"],
        user="0",
    )


@pytest.mark.parametrize("isolation", ["rootless", "oci"])
def test_buildah_can_use_stronger_isolation(
    isolation: str, task_runner_container: Container, context_dir: Path
) -> None:
    task_runner_container.run_cmd(
        ["buildah", "build", f"--isolation={isolation}", "."],
        volumes=[
            "/home/taskuser/.local/share/containers",
            f"{context_dir}:{context_dir}",
        ],
        workdir=context_dir,
        privileged=True,
    )


@pytest.mark.parametrize("isolation", ["rootless", "oci"])
def test_buildah_can_use_stronger_isolation_as_root(
    isolation: str, task_runner_container: Container, context_dir: Path
) -> None:
    task_runner_container.run_cmd(
        ["buildah", "build", f"--isolation={isolation}", "."],
        volumes=[
            "/var/lib/containers",
            f"{context_dir}:{context_dir}",
        ],
        workdir=context_dir,
        user="0",
        privileged=True,
    )


@pytest.mark.xfail(reason="Unfortunately, there is no easy way to make it work for arbitrary UIDs.")
def test_buildah_works_for_other_uids(task_runner_container: Container, context_dir: Path) -> None:
    task_runner_container.run_cmd(
        ["buildah", "build", "."],
        volumes=[
            "/home/taskuser/.local/share/containers",
            f"{context_dir}:{context_dir}",
        ],
        workdir=context_dir,
        user="1001:0",
    )
