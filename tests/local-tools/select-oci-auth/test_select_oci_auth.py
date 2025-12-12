import json
import pytest
import re
import tempfile
from pathlib import Path
from subprocess import run
from subprocess import CompletedProcess
from typing import Final

from tests.constants import REPO_ROOT

SCRIPT_FILE: Final = "select-oci-auth.sh"
SCRIPT_DIR: Final = REPO_ROOT / "local-tools" / "select-oci-auth"


@pytest.fixture
def auth_file(tmp_path) -> str:
    config_json = tmp_path / "config.json"
    auths = json.dumps(
        {
            "auths": {
                "docker.io": {"auth": "docker.io secret"},
                "https://index.docker.io/v1/": {"auth": "index.docker.io secret"},
                "quay.io/konflux-ci/foo": {"auth": "konflux-ci/foo secret"},
                "quay.io": {"auth": "quay secret"},
                "reg.io": {"auth": "reg.io secret"},
                "reg.io/foo/bar": {"auth": "reg.io/foo/bar secret"},
            }
        }
    )
    config_json.write_text(auths)
    return str(config_json)


def run_script(*args, auth_file: str | None = None) -> CompletedProcess:
    cmd = ["bash", SCRIPT_FILE, *args]
    # IMPORTANT: do not read auths from normal auth file.
    env = {"AUTHFILE": auth_file} if auth_file else None
    return run(cmd, env=env, cwd=SCRIPT_DIR, capture_output=True, text=True)


def test_print_usage_by_default():
    proc = run_script()
    assert proc.returncode == 0
    assert f"Usage: {SCRIPT_FILE}" in proc.stdout


def test_print_version():
    proc = run_script("--version")
    assert proc.returncode == 0
    assert re.fullmatch(r"\d+\.\d+\.\d+", proc.stdout.strip())


def test_print_usage():
    proc = run_script("--help")
    assert proc.returncode == 0
    assert f"Usage: {SCRIPT_FILE}" in proc.stdout


@pytest.mark.parametrize(
    "image_ref,expected_auth",
    [
        ["docker.io/library/debian:latest", '{"auths": {"docker.io": {"auth": "docker.io secret"}}}'],
        ["quay.io", '{"auths": {"quay.io": {"auth": "quay secret"}}}'],
        ["quay.io/foo", '{"auths": {"quay.io": {"auth": "quay secret"}}}'],
        ["quay.io/foo:0.1", '{"auths": {"quay.io": {"auth": "quay secret"}}}'],
        ["quay.io/foo:0.1@sha256:1234567", '{"auths": {"quay.io": {"auth": "quay secret"}}}'],
        ["quay.io/konflux-ci", '{"auths": {"quay.io": {"auth": "quay secret"}}}'],
        ["quay.io/konflux-ci/foo", '{"auths": {"quay.io": {"auth": "konflux-ci/foo secret"}}}'],
        ["quay.io/konflux-ci/foo:0.3", '{"auths": {"quay.io": {"auth": "konflux-ci/foo secret"}}}'],
        ["quay.io/konflux-ci/foo@sha256:1234567", '{"auths": {"quay.io": {"auth": "konflux-ci/foo secret"}}}'],
        ["quay.io/konflux-ci/foo:0.3@sha256:1234567", '{"auths": {"quay.io": {"auth": "konflux-ci/foo secret"}}}'],
        ["quay.io/konflux-ci/foo/bar", '{"auths": {"quay.io": {"auth": "konflux-ci/foo secret"}}}'],
        ["reg.io", '{"auths": {"reg.io": {"auth": "reg.io secret"}}}'],
        ["reg.io/foo", '{"auths": {"reg.io": {"auth": "reg.io secret"}}}'],
        ["reg.io/foo/bar", '{"auths": {"reg.io": {"auth": "reg.io/foo/bar secret"}}}'],
        ["new-reg.io/cool-app", '{"auths": {}}'],
        ["arbitrary-input", '{"auths": {}}'],
    ],
)
def test_select_auth(image_ref, expected_auth, auth_file):
    proc = run_script(image_ref, auth_file=auth_file)
    assert proc.returncode == 0
    assert proc.stdout.strip() == expected_auth


def test_fallback_search_for_docker_io(auth_file):
    # remove registry docker.io from auth file
    auths = json.loads(Path(auth_file).read_text())
    del auths["auths"]["docker.io"]
    Path(auth_file).write_text(json.dumps(auths))

    proc = run_script("docker.io/library/postgres", auth_file=auth_file)
    assert proc.returncode == 0
    expected = '{"auths": {"https://index.docker.io/v1/": {"auth": "index.docker.io secret"}}}'
    assert proc.stdout.strip() == expected
