import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import Self, Sequence

log = logging.getLogger(__name__)


def run(
    cmd: list[str | os.PathLike[str]], check: bool = True, capture_output: bool = True
) -> subprocess.CompletedProcess[str]:
    log.debug("%s", shlex.join(map(str, cmd)))
    proc = subprocess.run(cmd, capture_output=capture_output, text=True)
    if capture_output:
        if stdout := proc.stdout.rstrip("\n"):
            log.debug("stdout>\n%s", stdout)
        if stderr := proc.stderr.rstrip("\n"):
            log.error("stderr>\n%s", stderr)
    if check:
        proc.check_returncode()
    return proc


class Container:
    def __init__(self, image_name: str) -> None:
        self._image_name = image_name

    @property
    def image_name(self) -> str:
        return self._image_name

    @classmethod
    def build_image(cls, context_dir: Path, image_name: str) -> Self:
        run(
            ["buildah", "bud", "--tag", image_name, context_dir],
            check=True,
        )
        return cls(image_name)

    def run_cmd(
        self,
        cmd: Sequence[str | os.PathLike[str]],
        check: bool = True,
        capture_output: bool = True,
        volumes: Sequence[str] = (),
        devices: Sequence[str] = (),
        workdir: str | os.PathLike[str] | None = None,
        user: str | None = None,
        privileged: bool = False,
        cap_add: Sequence[str] = (),
        cap_drop: Sequence[str] = (),
    ) -> subprocess.CompletedProcess[str]:
        """Run a command in the container image.

        Subprocess params:

        :param cmd: The command to execute
        :param check: Raise an error if the command exits with a non-0 exit code
        :param capture_output: Capture the stdout and stderr of the command

        Container params:

        :param volumes: A list of --volume arguments. For arguments in the form
                        HOST_DIR:CONTAINER_DIR, if they don't include any options,
                        automatically adds the :z option.
        :param devices: A list of --device arguments.
        :param workdir: Set the --workdir for the container.
        :param user: Set the --user for the container.
        :param privileged: Run the container as --privileged
        :param cap_add: A list of capabilities to add with --cap-add.
        :param cap_drop: A list of capabilities to drop with --cap-drop.
        """
        buildah_from: list[str | os.PathLike[str]] = ["buildah", "from"]

        buildah_from.extend(["--security-opt", "label=type:container_runtime_t"])

        for volume in volumes:
            if volume.count(":") == 1:
                # This is /host-dir:/container-dir, add :z to avoid SELinux problems
                volume += ":z"
            buildah_from.append(f"--volume={volume}")

        for device in devices:
            buildah_from.append(f"--device={device}")

        if privileged:
            buildah_from.append("--cap-add=ALL")

        for cap in cap_add:
            buildah_from.append(f"--cap-add={cap}")

        for cap in cap_drop:
            buildah_from.append(f"--cap-drop={cap}")

        buildah_from.append(self._image_name)

        container_id = run(buildah_from).stdout.strip()

        buildah_run: list[str | os.PathLike[str]] = ["buildah", "run", container_id, "--", *cmd]
        if workdir:
            buildah_run.insert(2, f"--workingdir={str(workdir)}")
        if user:
            buildah_run.insert(2, f"--user={user}")

        try:
            return run(buildah_run, check=check, capture_output=capture_output)
        finally:
            run(["buildah", "rm", container_id])
