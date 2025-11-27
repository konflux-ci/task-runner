#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

# These seem to be commonly used when compiling Go tools, e.g.:
#   https://github.com/anchore/syft/blob/5b96d1d69d76098778be0f8556d1a63d1050239f/.goreleaser.yaml#L20-L21
#   https://github.com/mikefarah/yq/blob/588d0bb3dd6e3d2d8db66e4fc68761108d299abe/Makefile.variables#L10
# Their purpose is to reduce the size of the binaries by omitting debug info.
COMMON_LDFLAGS='-s -w'

get_version() {
    local module=$1
    local version
    version=$(go list -m -f '{{.Version}}' "$module")
    echo "${version#v}"
}

syft_version=$(get_version github.com/anchore/syft)
go install -ldflags "$COMMON_LDFLAGS -X main.version=$syft_version" github.com/anchore/syft/cmd/syft

go install -ldflags "$COMMON_LDFLAGS" github.com/mikefarah/yq/v4

tkn_version=$(get_version github.com/tektoncd/cli)
go install -ldflags "$COMMON_LDFLAGS -X github.com/tektoncd/cli/pkg/cmd/version.clientVersion=$tkn_version" github.com/tektoncd/cli/cmd/tkn
