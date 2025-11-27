#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

OUTPUT_DIR=${GOBIN:-$(go env GOPATH)/bin}

cd kubernetes
make kubectl
cp _output/bin/kubectl "$OUTPUT_DIR/kubectl"
cd ..
