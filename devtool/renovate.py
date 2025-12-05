from typing import Any

from devtool.software_list import GoPackage


def renovate_json(go_packages: list[GoPackage]) -> dict[str, Any]:
    return {
        "$schema": "https://docs.renovatebot.com/renovate-schema.json",
        "extends": ["config:recommended", "helpers:pinGitHubActionDigestsToSemver"],
        "schedule": ["* * * * *"],
        "prHourlyLimit": 0,  # unlimited
        "gitIgnoredAuthors": ["github-actions[bot]@users.noreply.github.com"],
        "git-submodules": {
            "enabled": True,
            "packageRules": [
                {
                    "matchManagers": ["git-submodules"],
                    "groupName": "Runner software",
                },
                {
                    # Use regex versioning scheme for oc, which doesn't have proper semver tags
                    "matchManagers": ["git-submodules"],
                    "matchPackageNames": ["https://github.com/openshift/oc.git"],
                    "versioning": "regex:^openshift-clients-(?<major>\\d+)\\.(?<minor>\\d+)\\.(?<patch>\\d+)-(?<build>\\d+)$",
                },
            ],
        },
        "gomod": {
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
                    "groupName": "Runner software",
                },
            ]
        },
        "rpm-lockfile": {
            "packageRules": [
                {
                    "matchFileNames": ["deps/rpm/*"],
                    "groupName": "Runner software",
                },
            ]
        },
        "dockerfile": {
            "packageRules": [
                {
                    "matchFileNames": ["Containerfile"],
                    "groupName": "Base images",
                },
                {
                    # Follow Golang version tags (1.x), not RHEL version tags (10.x)
                    "matchPackageNames": ["registry.access.redhat.com/ubi10/go-toolset"],
                    "allowedVersions": "< 2.0",
                },
            ]
        },
        "github-actions": {
            "packageRules": [
                {
                    "matchManagers": ["github-actions"],
                    "groupName": "GitHub Actions",
                },
            ]
        },
        # IMPORTANT: keep the top-level packageRules as minimal as possible!
        # When possible, nest the rules under $pkg_manager.packageRules.
        # Otherwise, there's a high risk that MintMaker's default configuration
        # will override your custom configuration :(
        "packageRules": [
            # At the time of writing this comment, Renovate has 11 different Python managers
            # and it's not easy to find out which ones you need. Leave this rule in the top-level
            # packageRules and let's hope MintMaker doesn't break it for us.
            {
                "matchDatasources": ["pypi"],
                "groupName": "Python dependencies",
            },
        ],
        # And run `go mod tidy` afterwards to update the dependencies of our direct
        #  dependencies **when necessary** (according to Go's Minimal Version Selection).
        "postUpdateOptions": ["gomodTidy"],
    }
