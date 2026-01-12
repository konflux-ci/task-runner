#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

# These seem to be commonly used when compiling Go tools, e.g.:
#   https://github.com/anchore/syft/blob/5b96d1d69d76098778be0f8556d1a63d1050239f/.goreleaser.yaml#L20-L21
#   https://github.com/mikefarah/yq/blob/588d0bb3dd6e3d2d8db66e4fc68761108d299abe/Makefile.variables#L10
# Their purpose is to reduce the size of the binaries by omitting debug info.
COMMON_LDFLAGS='-s -w'

install_tool() {
    local name=$1
    shift

    local version_attribute=""
    local tags=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --version-attr)
                version_attribute=$2
                shift 2
                ;;
            --tags)
                tags=$2
                shift 2
                ;;
            *)
                echo "unknown argument: $1" >&2
                return 1
                ;;
        esac
    done

    cd "$name"

    # 'go tool' also lists builtin tools, filter them out by looking for the '.' in domain names
    go tool | grep -F . | while read -r tool_pkg; do
        local ldflags=$COMMON_LDFLAGS
        if [[ -n "$version_attribute" ]]; then
            version=$(go list -f '{{.Module.Version}}' "$tool_pkg")
            ldflags+=" -X ${version_attribute}=${version#v}"
        fi

        go install -ldflags "$ldflags" -tags "$tags" "$tool_pkg"
    done

    cd ..
}

install_tool syft --version-attr "main.version"

install_tool yq

install_tool tkn --version-attr "github.com/tektoncd/cli/pkg/cmd/version.clientVersion"

install_tool cosign --version-attr "sigs.k8s.io/release-utils/version.gitVersion"

install_tool oras --version-attr "oras.land/oras/internal/version.BuildMetadata"

install_tool conftest --version-attr "github.com/open-policy-agent/conftest/internal/version.Version"

install_tool buildah --tags "seccomp,libsqlite3,exclude_graphdriver_btrfs"
