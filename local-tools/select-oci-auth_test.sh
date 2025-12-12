#!/usr/bin/env bash

SCRIPT_FILE=select-oci-auth.sh
SCRIPT="$(dirname "${BASH_SOURCE[0]}")/${SCRIPT_FILE}"
TEST_FILE="$(basename "${BASH_SOURCE[0]}")"
AUTHFILE=$(mktemp --suffix="-$TEST_FILE")
export AUTHFILE  # IMPORTANT: do not read auths from normal auth file.

setup() {
    auth_data='{
    "auths": {
        "https://index.docker.io/v1/": {"auth": "docker secret"},
        "quay.io/konflux-ci/foo": {"auth": "konflux-ci/foo secret"},
        "quay.io": {"auth": "quay secret"},
        "reg.io": {"auth": "reg.io secret"},
        "reg.io/foo/bar": {"auth": "reg.io/foo/bar secret"}
    }
}'
    printf "%s" "$auth_data" >"$AUTHFILE"
}

teardown() {
    rm -f "$AUTHFILE"
}

fail() {
    printf "[FAILURE] %s\n" "$1" >&2
    actual=$2
    expected=$3
    if [[ -n "$actual" && -n "$expected" ]]; then
        printf "actual:   %s\n" "$actual" >&2
        printf "expected: %s\n" "$expected" >&2
    fi
    exit 1
}

test_print_usage_by_default() {
    if ! bash "$SCRIPT" | grep -q "Usage: $SCRIPT_FILE"; then
        fail "Usage is not print when invoking without argument."
    fi
}


test_data="
docker.io/library/debian:latest '{\"auths\": {\"https://index.docker.io/v1/\": {\"auth\": \"docker secret\"}}}'
quay.io '{\"auths\": {\"quay.io\": {\"auth\": \"quay secret\"}}}'
quay.io/foo '{\"auths\": {\"quay.io\": {\"auth\": \"quay secret\"}}}'
quay.io/foo:0.1 '{\"auths\": {\"quay.io\": {\"auth\": \"quay secret\"}}}'
quay.io/foo:0.1@sha256:1234567 '{\"auths\": {\"quay.io\": {\"auth\": \"quay secret\"}}}'
quay.io/konflux-ci '{\"auths\": {\"quay.io\": {\"auth\": \"quay secret\"}}}'
quay.io/konflux-ci/foo '{\"auths\": {\"quay.io\": {\"auth\": \"konflux-ci/foo secret\"}}}'
quay.io/konflux-ci/foo:0.3 '{\"auths\": {\"quay.io\": {\"auth\": \"konflux-ci/foo secret\"}}}'
quay.io/konflux-ci/foo@sha256:1234567 '{\"auths\": {\"quay.io\": {\"auth\": \"konflux-ci/foo secret\"}}}'
quay.io/konflux-ci/foo:0.3@sha256:1234567 '{\"auths\": {\"quay.io\": {\"auth\": \"konflux-ci/foo secret\"}}}'
quay.io/konflux-ci/foo/bar '{\"auths\": {\"quay.io\": {\"auth\": \"konflux-ci/foo secret\"}}}'
reg.io '{\"auths\": {\"reg.io\": {\"auth\": \"reg.io secret\"}}}'
reg.io/foo '{\"auths\": {\"reg.io\": {\"auth\": \"reg.io secret\"}}}'
reg.io/foo/bar '{\"auths\": {\"reg.io\": {\"auth\": \"reg.io/foo/bar secret\"}}}'
"

test_select_by_image_repo() {
    while read -r arg expected_auth
    do
        if [[ -z "$arg" ]]; then
            continue
        fi
        actual=$(bash "$SCRIPT" "$arg")
        expected=$(tr -d \' <<<"$expected_auth")
        if [[ "$actual" != "$expected" ]]; then
            fail "Failed to select auth for $arg" "$actual" "$expected"
        fi
    done <<<"$test_data"
}

setup
test_print_usage_by_default
test_select_by_image_repo
teardown
