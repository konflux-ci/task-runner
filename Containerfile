FROM registry.access.redhat.com/ubi10/go-toolset:1.25@sha256:182645783ad0a0af4a78d928f2d9167815d59c12cc156aa3c229cf3a49d636d9 AS go-build

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


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1@sha256:28ec2f4662bdc4b0d4893ef0d8aebf36a5165dfb1d1dc9f46319bd8a03ed3365

COPY --from=go-build /deps/golang/bin/ /usr/local/bin/

COPY deps/rpm/ /tmp/rpm-installation/
RUN cd /tmp/rpm-installation && \
    ./install-rpms.sh && \
    rm -r /tmp/rpm-installation
