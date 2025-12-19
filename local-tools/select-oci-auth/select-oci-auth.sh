#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

VERSION="1.0.0"
declare -r VERSION

AUTHFILE="${AUTHFILE:-$HOME/.docker/config.json}"
declare -r AUTHFILE

print_version() {
    printf "%s\n" "$VERSION"
}

usage() {
    local script
    script="$(basename "${BASH_SOURCE[0]}")"
    local -r usage="\
$script selects the expected token from ~/.docker/config.json given an image reference.

The format of ~/.docker/config.json is not well defined. Some clients allow the specification of
repository specific tokens, e.g. buildah and kubernetes, while others only allow registry specific
tokens, e.g. oras. This script serves as an adapter to allow repository specific tokens for
clients that do not support it.

If the provided image reference contains a tag or a digest, those are ignored.

Usage: $script [--version] [--help] <image reference>

Example:

    $script quay.io/konflux-ci/foo
    $script quay.io/konflux-ci/foo:0.2.1
    $script quay.io/konflux-ci/foo:0.2.1@sha256:1234567
    $script quay.io/konflux-ci/bar/baz@sha256:1234567
"
    printf "%s\n" "$usage"
}

get_image_repo() {
    local -r image_ref=$1
    # Trim off both tag and digest from image reference
    # Trim off digest
    repo="$(printf "%s" "$image_ref" | cut -d@ -f1)"
    if [[ $(printf "%s" "$repo" | tr -cd ":" | wc -c | tr -d '[:space:]') == 2 ]]; then
        # format is now registry:port/repository:tag
        # trim off everything after the last colon
        repo=${repo%:*}
    elif [[ $(printf "%s" "$repo" | tr -cd ":" | wc -c | tr -d '[:space:]') == 1 ]]; then
        # we have either a port or a tag so inspect the content after
        # the colon to determine if it is a valid tag.
        # https://github.com/opencontainers/distribution-spec/blob/main/spec.md
        # [a-zA-Z0-9_][a-zA-Z0-9._-]{0,127} is the regex for a valid tag
        # If not a valid tag, leave the colon alone.
        if [[ "$(printf "%s" "$repo" | cut -d: -f2 | tr -d '[:space:]')" =~ ^([a-zA-Z0-9_][a-zA-Z0-9._-]{0,127})$ ]]; then
            # We match a tag so trim it off
            repo=$(printf "%s" "$repo" | cut -d: -f1)
        fi
    fi
    printf "%s" "$repo"
}

print_auth() {
    local -r registry=${1:-""}
    local -r token=${2:-""}
    if [[ -n "$registry" && -n "$token" ]]; then
        printf '{"auths": {"%s": %s}}' "$registry" "$token"
    else
        printf '{"auths": {}}'
    fi
}

select_auth() {
    local -r image_ref="$1"

    repo=$(get_image_repo "$image_ref")
    registry="${repo/\/*}"

    if [[ -f "$AUTHFILE" ]]; then
        while true; do
            token=$(< "$AUTHFILE" yq ".auths[\"$repo\"]")
            if [[ "$token" != "null" ]]; then
                >&2 printf "Using token for %s\n" "$repo"
                print_auth "$registry" "$token" | yq .
                exit 0
            fi

            if [[ "$repo" != *"/"* ]]; then
                break
            fi

            repo="${repo%*/*}"
        done

        # For docker.io, check auth key https://index.docker.io/v1/
        # oras-login writes this key.
        if [ "$registry" = "docker.io" ]; then
            registry="https://index.docker.io/v1/"
            token=$(< "$AUTHFILE" yq '.auths["'$registry'"]')
            if [[ "$token" != "null" ]]; then
                >&2 printf "Using token for %s\n" "$registry"
                print_auth "$registry" "$token" | yq .
                exit 0
            fi
        fi
    fi

    >&2 printf "Token not found for %s\n" "$image_ref"
    print_auth
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
        return 0
    fi
    case "$1" in
        --version) print_version ;;
        --help) usage ;;
        *) select_auth "$1" ;;
    esac
}

main "$@"
