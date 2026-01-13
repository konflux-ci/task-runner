FROM registry.access.redhat.com/ubi10/go-toolset:1.25.3@sha256:4d65503c0066e26df81fbfe93203f0e7dbc23cf503ca2972fef01cdc13cd813c AS go-build

USER 0

WORKDIR /deps/golang/tools
COPY deps/go-tools/ .
RUN GOBIN=/deps/golang/bin ./install-tools.sh

# Have to copy the whole repo including .git now, because that's
# where submodule tags are stored (and we need those for versioning)
WORKDIR /repo
COPY . .
RUN cd deps/go-submodules && \
    GOBIN=/deps/golang/bin ./install-submodules.sh


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1-1766033715@sha256:67aafc6c9c44374e1baf340110d4c835457d59a0444c068ba9ac6431a6d9e7ac

COPY --from=go-build /deps/golang/bin/ /usr/local/bin/

COPY deps/rpm/ /tmp/rpm-installation/
RUN cd /tmp/rpm-installation && \
    ./install-rpms.sh && \
    rm -r /tmp/rpm-installation

COPY deps/pip/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-binary :all: --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt && \
    microdnf -y remove gcc python3-devel python3-pip && \
    microdnf clean all

COPY local-tools/select-oci-auth/select-oci-auth.sh /usr/local/bin/select-oci-auth
COPY local-tools/retry/retry.sh                     /usr/local/bin/retry

ENV RETRY_STOP_IF_STDERR_MATCHES='unauthorized'

# Create a non root user whos home directory belongs to the root group.
RUN useradd -u 1000 -g 0 -s /bin/sh -d /home/taskuser taskuser && \
    chown -R 1000:0 /home/taskuser && \
    chmod -R 770 /home/taskuser
USER 1000
# Set HOME variable to a writable location.
# By default it's `/` and causes 'permission denied' problems when writing files.
# The above can cause issue to credentials propagation into Tekton task pods.
ENV HOME=/home/taskuser
