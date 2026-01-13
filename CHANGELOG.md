# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- `buildah` added (1.42.2)
- `crun` added (1.23.1-1.el10_0)
- `fuse-overlayfs` added (1.16-1.el10_1)

Note that using `buildah` may require extra configuration on the user's side.
See [docs/buildah.md](./docs/buildah.md) for more details.

## 1.1.1

Date: 2026-01-14

- Create a non root `taskuser` user to run task pod with.
- Set `HOME` environment variable to `/home/taskuser`
  and allow access to it to all users in the `root` group to avoid permission issues.
  It's needed in case the orchestrator changes user ID the container runs with.
  This is also important for Tekton credentials propagation into the task pods.
- `openssl` 3.5.1-4.el10_1 => 3.5.1-5.el10_1

## 1.1.0

Date: 2026-01-08

- `awscli` added (1.44.12)
- `conftest` 0.65.0 => 0.66.0
- `syft` 1.38.2 => 1.39.0
- `python3` 3.12.11-3.el10 => 3.12.12-1.el10_1
- `tar` 1.35-7.el10 => 1.35-9.el10_1

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
