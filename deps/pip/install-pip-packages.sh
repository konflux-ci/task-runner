#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

# Install pip packages from requirements.txt
#
# In hermetic builds (Konflux), cachi2 pre-fetches packages and sets:
#   PIP_FIND_LINKS - path to pre-fetched packages
#   PIP_NO_INDEX   - prevents access to PyPI
# pip automatically respects these environment variables.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ -n "${PIP_FIND_LINKS:-}" ]]; then
    echo "Hermetic build detected (PIP_FIND_LINKS=${PIP_FIND_LINKS})"
fi

pip3 install --no-cache-dir -r "$SCRIPT_DIR/requirements.txt"

