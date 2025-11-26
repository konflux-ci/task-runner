#!/bin/bash
set -o errexit -o nounset -o pipefail

syft_version=$(go list -m -f '{{.Version}}' github.com/anchore/syft)
go install -ldflags "-X main.version=${syft_version#v}" github.com/anchore/syft/cmd/syft

go install github.com/mikefarah/yq/v4
