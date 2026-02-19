#!/bin/bash
set -o errexit -o nounset -o pipefail -o xtrace

# Install or re-install the exact versions of RPMs specified in the lockfile.

list_packages_with_evrs() {
    local attribute=$1

    local packages
    packages=$(yq ".$attribute" rpms.in.yaml -o json --indent 0)

    if [[ "$packages" == null ]]; then
        return
    fi

    # shellcheck disable=SC2016
    arch=$(uname -m) input_packages="$packages" yq '
        (.arches[] | select(.arch == env(arch)) | .packages) as $resolved_packages |
        env(input_packages)[] as $pkg_name |
        $resolved_packages[] | select(.name == $pkg_name) |
        $pkg_name + "-" + .evr
    ' rpms.lock.yaml
}

if command -v microdnf >/dev/null; then
    dnf_cmd=(microdnf)
else
    dnf_cmd=(dnf)
fi

dnf_cmd+=(-y --setopt install_weak_deps=0)

mapfile -t packages < <(list_packages_with_evrs packages)
mapfile -t reinstall_packages < <(list_packages_with_evrs reinstallPackages)
mapfile -t upgrade_packages < <(list_packages_with_evrs upgradePackages)

all_packages=("${packages[@]}" "${reinstall_packages[@]}" "${upgrade_packages[@]}")

"${dnf_cmd[@]}" install "${all_packages[@]}"

