#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

VERSION="1.0.0"
SCRIPT_NAME=$(basename "${BASH_SOURCE[0]}")

# Configuration
: "${RETRY_BASE_DELAY=1}"
: "${RETRY_FACTOR=2}"
: "${RETRY_MAX_TRIES=10}"
: "${RETRY_STOP_IF_STDERR_MATCHES=}"
: "${RETRY_STOP_ON_EXIT_CODES=}"

print_version() {
    printf "%s %s\n" "$SCRIPT_NAME" "$VERSION"
}

print_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [--version] <command>

Re-runs the provided command until it suceeds or until the maximum number of attempts
is reached. Follows exponential backoff between attempts. Specifically, the wait time
before a retry follows this formula:

    wait_before(N-th retry) = base * backoff_factor ** (N - 1)

With base=1, backoff_factor=2 and 10 total attempts, the wait sequence is:
    [1, 2, 4, 8, 16, 32, 64, 128, 256]

Configuration (environment variables):

    RETRY_BASE_DELAY=$RETRY_BASE_DELAY
        The base of the backoff sequence (see the formula above)

    RETRY_FACTOR=$RETRY_FACTOR
        The backoff factor (see the formula above)

    RETRY_MAX_TRIES=$RETRY_MAX_TRIES
        The total number of attempts (including the initial one)

    RETRY_STOP_IF_STDERR_MATCHES=$RETRY_STOP_IF_STDERR_MATCHES
        Stop retrying if the stderr contains this pattern ('grep -i -E' semantics)

    RETRY_STOP_ON_EXIT_CODES=$RETRY_STOP_ON_EXIT_CODES
        Stop retrying if the exit code is one of these comma-separated exit codes.
        If empty or unset, stops only on success (exit code 0).

Example:

    $SCRIPT_NAME buildah push quay.io/konflux-ci/foo:0.2.1

    # skopeo returns 2 for e.g. non-existent image
    export RETRY_STOP_ON_EXIT_CODES=2
    $SCRIPT_NAME skopeo inspect --raw docker://quay.io/konflux-ci/foo@sha256:1234567
EOF
}

log() {
    local format_string="[retry] $1\n"
    shift

    # shellcheck disable=SC2059  # we intentionally use a variable as the format string
    printf "$format_string" "$@" >&2
}

retry() {
    local status

    local error_file
    error_file=$(mktemp --tmpdir 'retry.XXXXXX')
    trap 'rm "$error_file"' RETURN

    local stop_on_exit_codes=()
    IFS=',' read -r -a stop_on_exit_codes <<< "$RETRY_STOP_ON_EXIT_CODES"

    for i in $(seq 1 "$RETRY_MAX_TRIES"); do
        local nth_retry=$((i - 1))
        local waittime
        if [[ $nth_retry -gt 0 ]]; then
            # Bash doesn't natively support floating-point math, use 'bc'
            waittime=$(bc -l <<< "$RETRY_BASE_DELAY * $RETRY_FACTOR ^ ($nth_retry - 1)")
            log "waiting for %g seconds before attempt %d..." "$waittime" "$i"
            sleep "$waittime"
        fi

        log "executing:%s" "$(printf ' %q' "${@}")"

        # Print stderr while executing but also write it to $error_file
        if "$@" 2> >(tee "$error_file" >&2); then
            return 0
        else
            status=$?
        fi

        for stop_on_code in "${stop_on_exit_codes[@]}"; do
            if [[ $status -eq "$stop_on_code" ]]; then
                log "giving up after %d attempts: exit code is %d" "$i" "$status"
                return "$status"
            fi
        done

        if [[ -n "$RETRY_STOP_IF_STDERR_MATCHES" ]]; then
            if grep -i -E -q "$RETRY_STOP_IF_STDERR_MATCHES" "$error_file"; then
                log "giving up after %d attempts: stderr matches '%s'" \
                    "$i" "$RETRY_STOP_IF_STDERR_MATCHES"
                return "$status"
            fi
        fi
    done

    log "giving up after %d attempts: max attempts reached" "$RETRY_MAX_TRIES"
    return "$status"
}

check_dependencies() {
    for cmd in bc grep; do
        if ! command -v "$cmd" >/dev/null; then
            log "error: missing '%s' executable" "$cmd"
            return 1
        fi
    done
}

case ${1:-'--help'} in
    --version) print_version ;;
    --help) print_usage ;;
    *)
        check_dependencies
        retry "$@"
        ;;
esac
