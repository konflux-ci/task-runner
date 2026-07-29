# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Installed Software

- `olot` 0.1.18 => 1.1.0

## 2.1.0

Date: 2026-07-08

### Installed Software

- `git-lfs` added (3.7.1-5.el10_2.5)
- `cosign` 3.0.5 => 3.1.1
- `huggingface-hub` 1.17.0 => 1.22.0
- `oc` 4.21.0 => 4.22.0
- `syft` 1.44.0 => 1.46.0
- `awscli` 1.45.18 => 1.45.40
- `coreutils-single` 9.5-7.el10 => 9.5-8.el10_2
- `kubectl` 1.36.1 => 1.36.2
- `olot` 0.1.17 => 0.1.18
- `openssl` 3.5.5-3.el10_2 => 3.5.5-4.el10_2
- `rsync` 3.4.1-6.el10_2 => 3.4.4-1.el10_2
- `skopeo` 1.22.2-1.el10_2 => 1.22.2-2.el10_2
- `tkn` 0.44.1 => 0.44.2
- `yq` 4.53.2 => 4.53.3

### Added

- Added `git-lfs` to support cloning LFS-enabled repositories in the
  [git-clone] task and its derived production variants.

[git-clone]: https://github.com/konflux-ci/build-definitions/tree/main/task/git-clone

## 2.0.0

Date: 2026-06-16

Major version upgrade of cosign

### Installed Software

- `cosign` 2.6.3 => 3.0.5

## 1.8.1

Date: 2026-06-05

Re-release of 1.8.0 with no changes. The 1.8.0 release did not trigger CI pipelines.

## 1.8.0

> [!WARNING]
> This release did not properly trigger CI pipelines, re-released as 1.8.1.

Date: 2026-06-05

### Installed Software

- `buildah` 1.43.1 => 1.44.0
- `git-core` 2.47.3-1.el10_0 => 2.52.0-1.el10
- `huggingface-hub` 1.13.0 => 1.17.0
- `kubectl` 1.35.2 => 1.36.1
- `skopeo` 1.20.0-3.el10_1 => 1.22.2-1.el10_2
- `awscli` 1.45.2 => 1.45.18
- `coreutils-single` 9.5-6.el10 => 9.5-7.el10
- `crun` 1.27-1.el10_1 => 1.27-2.el10_2
- `curl` 8.12.1-2.el10_1.2 => 8.12.1-4.el10
- `jq` 1.7.1-11.el10_1.0.2 => 1.7.1-11.el10_2.2
- `openssh-clients` 9.9p1-14.el10_1 => 9.9p1-23.el10_2
- `openssl` 3.5.1-7.el10_1 => 3.5.5-3.el10_2
- `oras` 1.3.0 => 1.3.2
- `python3` 3.12.12-3.el10_1.3 => 3.12.13-2.el10_2
- `rpm` 4.19.1.1-20.el10 => 4.19.1.1-23.el10
- `rsync` 3.4.1-2.el10_1.2 => 3.4.1-6.el10_2
- `sed` 4.9-3.el10 => 4.9-5.el10
- `subscription-manager` 1.30.10.1-1.el10_1 => 1.30.12-1.el10
- `tar` 1.35-9.el10_1 => 1.35-11.el10

### Changed

- Buildah configuration:
  - Set `engine.image_copy_tmp_dir = <containers storage path>` in [containers.conf]
    to work around [buildah#6892]. This results in some temporary files being written
    to the storage root (`/var/lib/containers/storage` for the root user).
    Buildah does seem to clean them up after every build.

### Known Issues

- Buildah:
  - `BUILDAH_ISOLATION=oci` doesn't work due to [buildah#6891]. If you're overriding
    the task-runner default (`BUILDAH_ISOLATION=chroot`), please use `rootless` instead.
  - Due to [buildah#6890], `buildah build` is unable to fall back to `fuse-overlayfs`
    when the kernel-native overlay implementation is unavailable. Please see
    [docs/buildah.md](docs/buildah.md) for guidance on how to enable native overlay
    or alternatives.

[containers.conf]: https://www.mankier.com/5/containers.conf
[buildah#6890]: https://github.com/podman-container-tools/buildah/issues/6890
[buildah#6891]: https://github.com/podman-container-tools/buildah/issues/6891
[buildah#6892]: https://github.com/podman-container-tools/buildah/issues/6892

## 1.7.0

Date: 2026-05-14

### Installed Software

- `openssh-clients` added (9.9p1-14.el10_1)
- `rsync` added (3.4.1-2.el10_1.2)
- `subscription-manager` added (1.30.10.1-1.el10_1)
- `awscli` 1.44.49 => 1.45.2
- `conftest` 0.66.0 => 0.68.2
- `crun` 1.23.1-1.el10_0 => 1.27-1.el10_1
- `huggingface-hub` 1.7.1 => 1.13.0
- `syft` 1.42.1 => 1.44.0
- `yq` 4.52.2 => 4.53.2
- `buildah` 1.43.0 => 1.43.1
- `cosign` 2.6.2 => 2.6.3
- `jq` 1.7.1-11.el10 => 1.7.1-11.el10_1.0.2
- `olot` 0.1.16 => 0.1.17
- `python3` 3.12.12-3.el10_1.1 => 3.12.12-3.el10_1.3
- `tkn` 0.44.0 => 0.44.1

### Added

- `rsync`, `ssh` and `subscription-manager`
- The container image now has a floating `v1` tag pointing to the latest 1.x release:
  [`quay.io/konflux-ci/task-runner:v1`](https://quay.io/konflux-ci/task-runner:v1)

### Fixed

- The `version` label in the container image is now correct
  (previously, this label was inherited from the UBI base image)

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
