#!/bin/bash
set -o errexit -o nounset -o pipefail

# Helper script for retry tests

# Always succeeds
succeed() {
    echo "Success!"
    exit 0
}

# Always fails with exit code 1
fail() {
    echo "Error: command failed" >&2
    exit 1
}

# Fails with specific exit code
fail_with_code() {
    local code="${1:-1}"
    echo "Error: command failed with code $code" >&2
    exit "$code"
}

# Fails with stderr pattern
fail_with_stderr() {
    local error="${1:-unauthorized}"
    echo "Error: $error" >&2
    exit 1
}

# Fails N times, then succeeds (uses a counter file)
fail_then_succeed() {
    local max_failures="$1"
    local state_file="$2"

    local count=0
    if [[ -f "$state_file" ]]; then
        count=$(cat "$state_file")
    fi

    if [[ $count -lt $max_failures ]]; then
        count=$((count + 1))
        echo "$count" > "$state_file"
        echo "Attempt $count failed" >&2
        exit 1
    else
        echo "Success after $count attempts!"
        exit 0
    fi
}

case "${1:-}" in
    succeed) succeed ;;
    fail) fail ;;
    fail_with_code) fail_with_code "$2" ;;
    fail_with_stderr) fail_with_stderr "$2" ;;
    fail_then_succeed) fail_then_succeed "$2" "$3" ;;
    *)
        echo "Usage: $0 {succeed|fail|fail_with_code|fail_with_stderr|fail_then_succeed}" >&2
        exit 1
        ;;
esac
