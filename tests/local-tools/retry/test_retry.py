import os
import re
import subprocess
import time
from pathlib import Path

from tests.constants import REPO_ROOT

SCRIPT_FILE = "retry.sh"
SCRIPT_DIR = REPO_ROOT / "local-tools" / "retry"
HELPER_SCRIPT = Path(__file__).parent / "test-helper.sh"


def run_retry(
    *args: str | os.PathLike[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the retry script with the specfied arguments and environment variables."""
    default_env = {"RETRY_BASE_DELAY": "0.001", "RETRY_MAX_TRIES": "3"}
    if env:
        default_env.update(env)

    return subprocess.run(
        ["bash", SCRIPT_FILE, *args],
        env=default_env,
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )


def test_print_usage_by_default() -> None:
    proc = run_retry()
    assert proc.returncode == 0
    assert f"Usage: {SCRIPT_FILE}" in proc.stdout


def test_print_version() -> None:
    proc = run_retry("--version")
    assert proc.returncode == 0
    assert re.fullmatch(r"[\w.]+ \d+\.\d+\.\d+", proc.stdout.strip())


def test_print_usage() -> None:
    proc = run_retry("--help")
    assert proc.returncode == 0
    assert f"Usage: {SCRIPT_FILE}" in proc.stdout


def test_successful_command_no_retry() -> None:
    proc = run_retry("bash", HELPER_SCRIPT, "succeed")
    assert proc.returncode == 0
    assert "Success!" in proc.stdout
    # Should only execute once
    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] waiting for" not in proc.stderr


def test_command_succeeds_after_retries(tmp_path: Path) -> None:
    state_file = tmp_path / "state"

    # Command will fail 2 times, then succeed on attempt 3
    proc = run_retry("bash", HELPER_SCRIPT, "fail_then_succeed", "2", state_file)
    assert proc.returncode == 0
    assert "Success after 2 attempts!" in proc.stdout
    # Should execute 3 times total
    assert proc.stderr.count("[retry] executing:") == 3
    # Should wait before attempts 2 and 3
    assert proc.stderr.count("[retry] waiting for") == 2


def test_command_fails_all_attempts() -> None:
    proc = run_retry("bash", HELPER_SCRIPT, "fail")
    assert proc.returncode == 1
    assert "Error: command failed" in proc.stderr
    # Should execute 3 times (RETRY_MAX_TRIES=3)
    assert proc.stderr.count("[retry] executing:") == 3
    # Should wait before attempts 2 and 3
    assert proc.stderr.count("[retry] waiting for") == 2
    assert "[retry] giving up after 3 attempts: max attempts reached" in proc.stderr


def test_exponential_backoff_timing(tmp_path: Path) -> None:
    state_file = tmp_path / "state"

    start_time = time.time()
    # Command will fail 4 times, then succeed on attempt 5
    # With RETRY_BASE_DELAY=0.001, RETRY_FACTOR=2:
    # Wait times: 0.001, 0.002, 0.004, 0.008 = 0.015 seconds total
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_then_succeed",
        "4",
        state_file,
        env={"RETRY_MAX_TRIES": "5"},
    )
    elapsed_time = time.time() - start_time

    assert proc.returncode == 0
    # Should take at least 0.015 seconds for the waits
    assert elapsed_time >= 0.015

    # Verify exponential backoff sequence in stderr
    assert "[retry] waiting for 0.001 seconds before attempt 2" in proc.stderr
    assert "[retry] waiting for 0.002 seconds before attempt 3" in proc.stderr
    assert "[retry] waiting for 0.004 seconds before attempt 4" in proc.stderr
    assert "[retry] waiting for 0.008 seconds before attempt 5" in proc.stderr


def test_stop_on_exit_code() -> None:
    # Configure to stop on exit code 42
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_with_code",
        "42",
        env={"RETRY_STOP_ON_EXIT_CODES": "42"},
    )
    assert proc.returncode == 42
    # Should execute only once and stop
    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] giving up after 1 attempts: exit code is 42" in proc.stderr
    assert "[retry] waiting for" not in proc.stderr


def test_stop_on_multiple_exit_codes() -> None:
    # Configure to stop on exit codes 2 or 42
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_with_code",
        "2",
        env={"RETRY_STOP_ON_EXIT_CODES": "2,42"},
    )
    assert proc.returncode == 2
    # Should execute only once and stop
    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] giving up after 1 attempts: exit code is 2" in proc.stderr


def test_stop_if_stderr_matches() -> None:
    # Configure to stop if stderr matches "unauthorized"
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_with_stderr",
        "unauthorized",
        env={"RETRY_STOP_IF_STDERR_MATCHES": "unauthorized"},
    )
    assert proc.returncode == 1
    # Should execute only once and stop
    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] giving up after 1 attempts: stderr matches 'unauthorized'" in proc.stderr
    assert "[retry] waiting for" not in proc.stderr


def test_stop_if_stderr_matches_case_insensitive() -> None:
    # Pattern matching should be case-insensitive
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_with_stderr",
        "UNAUTHORIZED",
        env={"RETRY_STOP_IF_STDERR_MATCHES": "unauthorized"},
    )
    assert proc.returncode == 1
    # Should execute only once and stop
    assert proc.stderr.count("[retry] executing:") == 1
    assert "[retry] giving up after 1 attempts: stderr matches 'unauthorized'" in proc.stderr


def test_custom_retry_parameters(tmp_path: Path) -> None:
    state_file = tmp_path / "state"

    # Test with custom RETRY_MAX_TRIES and RETRY_BASE_DELAY
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_then_succeed",
        "3",
        state_file,
        env={"RETRY_MAX_TRIES": "4", "RETRY_BASE_DELAY": "0.005", "RETRY_FACTOR": "2"},
    )
    assert proc.returncode == 0
    # Should execute 4 times total
    assert proc.stderr.count("[retry] executing:") == 4
    # Should wait 3 times
    assert proc.stderr.count("[retry] waiting for") == 3
    # Verify first wait time with custom base
    assert "[retry] waiting for 0.005 seconds before attempt 2" in proc.stderr


def test_retries_continue_when_exit_code_not_in_stop_list(tmp_path: Path) -> None:
    state_file = tmp_path / "state"

    # Command fails with exit code 1, but stop list only has 42
    # So it should retry
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_then_succeed",
        "2",
        state_file,
        env={"RETRY_STOP_ON_EXIT_CODES": "42"},
    )
    assert proc.returncode == 0
    # Should retry and eventually succeed
    assert proc.stderr.count("[retry] executing:") == 3


def test_retries_continue_when_stderr_does_not_match(tmp_path: Path) -> None:
    state_file = tmp_path / "state"

    # stderr will contain "Attempt N failed" but not "unauthorized"
    proc = run_retry(
        "bash",
        HELPER_SCRIPT,
        "fail_then_succeed",
        "2",
        state_file,
        env={"RETRY_STOP_IF_STDERR_MATCHES": "unauthorized"},
    )
    assert proc.returncode == 0
    # Should retry and eventually succeed
    assert proc.stderr.count("[retry] executing:") == 3
