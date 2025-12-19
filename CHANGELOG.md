# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

*Nothing yet.*

## 1.0.0

Date: 2025-12-19

- `bc` added (1.07.1-23.el10)
- `retry` added (1.0.0)
- `select-oci-auth` added (1.0.0)
- `kubectl` 1.34.3 => 1.35.0
- `yq` 4.49.2 => 4.50.1
- `skopeo` 1.20.0-1.el10 => 1.20.0-2.el10_1

With the addition of the `retry` and `select-oci-auth` tools (more info in the
Local Tools section in the README), the runner image is now a true drop-in replacement
for the `quay.io/konflux-ci/appstudio-utils` image (and many other Task images).

This marks the 1.0.0 release of the image (which is backwards compatible with 0.x).

## 0.2.0

Date: 2025-12-11

- `kubectl` 1.34.2 => 1.34.3
- `syft` 1.38.0 => 1.38.2

### Added

- s390x and ppc64le builds of the container image

## 0.1.0

Date: 2025-12-10

The initial release of the task-runner image! 🎉

### Added

- All the software listed in
  <https://github.com/konflux-ci/task-runner/blob/v0.1.0/Installed-Software.md>
