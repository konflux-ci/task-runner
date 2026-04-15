FROM quay.io/konflux-ci/rust-builder:1.94.1@sha256:218cfc136260fb9a7c3f2cde2c8995664297ff59fd880258115ad87688dbc330 AS rust-builder

FROM registry.access.redhat.com/ubi10/go-toolset:1.25.8@sha256:535f003685bf49ce97d9948e8f02ec228e69a7f37e4952c976f09020938d826d AS go-build

USER 0

# Install dependencies for compiling buildah
RUN dnf -y install \
        bzip2 \
        glib2-devel \
        gpgme-devel \
        libassuan-devel \
        libseccomp-devel

WORKDIR /deps/golang/tools
COPY deps/go-tools/ .
RUN GOBIN=/deps/golang/bin ./install-tools.sh

# Have to copy the whole repo including .git now, because that's
# where submodule tags are stored (and we need those for versioning)
WORKDIR /repo
COPY . .
RUN cd deps/go-submodules && \
    GOBIN=/deps/golang/bin ./install-submodules.sh


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1-1776071394@sha256:7fabf2ff42ba1c2b3e4efcdd9ae25de0bce0592edf59151b41e58057b40898ce

COPY --from=go-build /deps/golang/bin/ /usr/local/bin/

COPY deps/rpm/ /tmp/rpm-installation/
RUN cd /tmp/rpm-installation && \
    ./install-rpms.sh && \
    rm -r /tmp/rpm-installation

COPY --from=rust-builder /usr/local/share/rust /usr/local/share/rust
COPY deps/pip/requirements.txt /tmp/requirements.txt
RUN microdnf -y install gcc python3-devel python3-pip && \
    export PATH="$PATH:/usr/local/share/rust/bin" && \
    pip3 install --no-binary :all: --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt && \
    rm -r /usr/local/share/rust && \
    microdnf -y remove gcc python3-devel python3-pip && \
    microdnf clean all

COPY local-tools/select-oci-auth/select-oci-auth.sh /usr/local/bin/select-oci-auth
COPY local-tools/retry/retry.sh                     /usr/local/bin/retry

ENV RETRY_STOP_IF_STDERR_MATCHES='unauthorized'

# Create a non root user whos home directory belongs to the root group.
RUN useradd -u 1000 -g 0 -s /bin/sh -d /home/taskuser taskuser && \
    chown -R 1000:0 /home/taskuser && \
    chmod -R 770 /home/taskuser

# Define subuid and subgid ranges that fit within 2^16 for root and taskuser.
# Without this, attempting to run containers inside the task-runner container would
# likely result in failure when trying to use a UID that isn't available in the userns.
RUN echo "root:1:65535" | tee /etc/sub{uid,gid} && \
    echo "taskuser:1001:64535" | tee -a /etc/sub{uid,gid}

USER 1000
# Set HOME variable to a writable location.
# By default it's `/` and causes 'permission denied' problems when writing files.
# The above can cause issue to credentials propagation into Tekton task pods.
ENV HOME=/home/taskuser

ENV BUILDAH_ISOLATION=chroot

WORKDIR /home/taskuser
