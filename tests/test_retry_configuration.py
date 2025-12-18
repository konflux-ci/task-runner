from tests.utils.container import Container


def test_retries_stop_on_unauthorized(task_runner_container: Container) -> None:
    proc = task_runner_container.run_cmd(
        [
            "retry",
            "bash",
            "-c",
            "echo Unauthorized >&2; exit 1",
        ],
        check=False,
    )
    assert proc.returncode == 1

    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] giving up after 1 attempts: stderr matches 'unauthorized'" in proc.stderr
