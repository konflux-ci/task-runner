#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

OUTPUT_DIR=${GOBIN:-$(go env GOPATH)/bin}
mkdir -p "$OUTPUT_DIR"

# Prevent kubectl from trying to download a different toolchain
export GOTOOLCHAIN=local

cd kubernetes
make kubectl
if [[ -f _output/bin/kubectl ]]; then
    cp _output/bin/kubectl "$OUTPUT_DIR/kubectl"
elif [[ -f _output/local/go/bin/kubectl ]]; then
    cp _output/local/go/bin/kubectl "$OUTPUT_DIR/kubectl"
else
    echo "Error: built kubectl not found in _output/bin nor _output/local/go/bin" >&2
    exit 1
fi
cd ..

cd oc
oc_version=$(git tag --points-at=HEAD | grep -E '[0-9]+\.[0-9]+\.[0-9]+' --only-matching)
make oc OS_GIT_VERSION="$oc_version"
cp ./oc "$OUTPUT_DIR/oc"
cd ..
