# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- The container image now has a floating `v1` tag pointing to the latest 1.x release:
  [`quay.io/konflux-ci/task-runner:v1`](https://quay.io/konflux-ci/task-runner:v1)

## 1.6.0

Date: 2026-03-24

- `huggingface-hub` added (1.7.1)
- `olot` added (0.1.16)
- `python3` 3.12.12-3.el10_1 => 3.12.12-3.el10_1.1

## 1.5.0

Date: 2026-03-13

- `buildah` 1.42.2 => 1.43.0
- `tkn` 0.43.0 => 0.44.0
- `awscli` 1.44.29 => 1.44.49
- `skopeo` 1.20.0-2.el10_1 => 1.20.0-3.el10_1

## 1.4.1

Date: 2026-02-19

### Fixed

Version 1.4.0 had mismatched RPM versions between architectures, which prevented
the release from succeeding. Re-generated RPM lockfiles to resolve this mismatch.

## 1.4.0

> [!WARNING]
> This release was unsuccessful, see 1.4.1 instead.

Date: 2026-02-19

- `syft` 1.41.1 => 1.42.1
- `curl` 8.12.1-2.el10 => 8.12.1-2.el10_1.2
- `python3` 3.12.12-1.el10_1 => 3.12.12-3.el10_1

## 1.3.0

Date: 2026-02-03

- `syft` 1.39.0 => 1.41.1
- `yq` 4.50.1 => 4.52.2
- `awscli` 1.44.12 => 1.44.29
- `cosign` 2.6.1 => 2.6.2
- `openssl` 3.5.1-5.el10_1 => 3.5.1-7.el10_1
- Set default `WORKDIR` to `/home/taskuser` (previously `/`).


## 1.2.0

Date: 2026-01-21

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
