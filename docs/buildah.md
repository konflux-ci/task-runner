# Buildah Configuration

While most of the tools included in the Task Runner image will work out of the box,
Buildah will not. There's a couple things you need to know if you want to use this
image for container-in-container workflows (i.e. for building or running containers
using Buildah).

- [Storage Driver](#storage-driver)
  - [Overlay](#overlay)
    - [Native](#native)
    - [fuse-overlayfs](#fuse-overlayfs)
  - [VFS](#vfs)
- [Isolation Mechanism](#isolation-mechanism)
  - [chroot](#chroot)
  - [oci, rootless](#oci-rootless)
- [Sample configurations](#sample-configurations)
  - [Non-root with native overlayfs](#non-root-with-native-overlayfs)
  - [Root with native overlayfs](#root-with-native-overlayfs)

## Storage Driver

### Overlay

By default, the Task Runner image configures Buildah to use the `overlay` storage
driver. This storage driver is compatible with container-in-container workflows,
with some conditions.

#### Native

Depending on the kernel version and various other properties of the host system,
it may be possible to use the kernel-native overlayfs implementation. This requires
mounting a volume over the container storage directory:

- `/var/lib/containers` when running as root
- `/home/taskuser/.local/share/containers` when running as `taskuser`

(E.g. `podman run -v /var/lib/containers -u 0 quay.io/konflux-ci/task-runner ...`)

#### fuse-overlayfs

In cases when it's not possible to use the native overlayfs implementation, Buildah
will try to fall back to fuse-overlayfs. This requires `/dev/fuse` to be available
(e.g. `podman run --device /dev/fuse quay.io/konflux-ci/task-runner ...`).

### VFS

If neither the native overlay nor fuse-overlayfs are an option, you can fall back
to the VFS storage driver by setting the `STORAGE_DRIVER=vfs` environment variable.

We don't recommend this, as VFS performs much worse than overlay.

## Isolation Mechanism

See also [`--isolation`](https://www.mankier.com/1/buildah-build#--isolation) in
the Buildah manpage.

### chroot

By default, the Task Runner image sets the `BUILDAH_ISOLATION=chroot` variable.
This is a much weaker isolation mechanism than the alternatives, but is much
easier to use for container-in-container workflows.

### oci, rootless

These are the full-fledged isolation mechanisms. It *is* possible to make them
work for container-in-container workflows, but typically requires elevated
permissions for the outer container (e.g. making the container privileged).

To put it differently:

- The `chroot` mechanism provides weak isolation between the inner container
  (e.g. the RUN instructions in a Containerfile) and the outer container
  (e.g. a Kubernetes Pod).
- The `oci` or `rootless` mechanisms provide strong isolation between the inner
  and outer containers, but enabling them requires weakening the isolation
  between the outer container and the underlying machine (e.g. a Kubernetes Node).

We generally recommend sticking with `chroot`.

## Sample configurations

### Non-root with native overlayfs

- Run as `taskuser` (UID 1000)
  - Note: other UIDs won't work due to missing entries in `/etc/subuid` and `/etc/subgid`
- Mount a volume over `/home/taskuser/.local/share/containers`
- Allow the `SETUID` and `SETGID` capabilities
- Allow other capabilities if necessary (e.g. `SYS_CHROOT`)
- Allow privilege escalation

Kubernetes pod:

```yaml
spec:
  volumes:
    - name: containers-storage
      emptyDir: {}

  containers:
    - image: quay.io/konflux-ci/task-runner
      volumeMounts:
        - name: containers-storage
          mountPath: /home/taskuser/.local/share/containers
      securityContext:
        runAsUser: 1000
        allowPrivilegeEscalation: true
        capabilities:
          add:
            - SETUID
            - SETGID
```

### Root with native overlayfs

- Run as root
- Mount a volume over `/var/lib/containers`
- Allow the `SETUID`, `SETGID` and `SETFCAP` capabilities
- Allow other capabilities if necessary (e.g. `SYS_CHROOT`)

Kubernetes pod:

```yaml
spec:
  volumes:
    - name: containers-storage
      emptyDir: {}

  containers:
    - image: quay.io/konflux-ci/task-runner
      volumeMounts:
        - name: containers-storage
          mountPath: /var/lib/containers
      securityContext:
        runAsUser: 0
        capabilities:
          add:
            - SETUID
            - SETGID
            - SETFCAP
```
