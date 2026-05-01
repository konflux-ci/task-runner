FROM quay.io/konflux-ci/rust-builder:1.94.1@sha256:8e84d5507f664cd2d3c6dfa1ad5ac33c3fd13480d6571c4ec1b9c3d26a28f0bc AS rust-builder

FROM registry.access.redhat.com/ubi10/go-toolset:1.25.9@sha256:5b8444b6540e82fa669086a122e76cd42fd750284505bc622bfc3d38b97664e8 AS go-build

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


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1-1776834797@sha256:2a4785f399dc7ae2f3ca85f68bac0ccac47f3e73464a47c21e4f7ae46b55a053

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
