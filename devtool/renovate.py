from typing import Any

from devtool.software_list import GoPackage


def renovate_json(go_packages: list[GoPackage]) -> dict[str, Any]:
    return {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": ["config:recommended"],
        # Run bi-weekly on the 1st and 15th of each month
        "schedule": ["* * 1,15 * *"],
        "prHourlyLimit": 0,  # unlimited
        "git-submodules": {
            "enabled": True,
        },
        "packageRules": [
            {
                "matchManagers": ["gomod"],
                "enabled": False,
            },
            {
                # Don't update any Go dependencies unless they're the direct dependencies
                # that we care about. Updating indirect dependencies could cause unexpected
                # behavior when the upstream tool builds with an older version of a library
                # and we build with a newer version.
                "matchManagers": ["gomod"],
                "matchPackageNames": [p.module_path for p in go_packages],
                "enabled": True,
                "groupName": "Go tools",
            },
            {
                "matchDatasources": ["pypi"],
                "groupName": "Python dependencies",
            },
            {
                "matchManagers": ["git-submodules"],
                "groupName": "Git submodules",
            },
            {
                # Use regex versioning scheme for oc, which doesn't have proper semver tags
                "matchManagers": ["git-submodules"],
                "matchPackageNames": ["https://github.com/openshift/oc.git"],
                "versioning": "regex:^openshift-clients-(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)-(?<build>\\d+)$",
            },
            {
                "matchFileNames": ["Containerfile"],
                "groupName": "Base images",
            },
            {
                # Follow Golang version tags (1.x), not RHEL version tags (10.x)
                "matchPackageNames": ["registry.access.redhat.com/ubi10/go-toolset"],
                "allowedVersions": "< 2.0",
            },
        ],
        # And run `go mod tidy` afterwards to update the dependencies of our direct
        #  dependencies **when necessary** (according to Go's Minimal Version Selection).
        "postUpdateOptions": ["gomodTidy"],
    }
