FROM registry.access.redhat.com/ubi10/go-toolset:1.25.3@sha256:182645783ad0a0af4a78d928f2d9167815d59c12cc156aa3c229cf3a49d636d9 AS go-build

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


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1-1764604111@sha256:a13cec4e2e30fa2ca6468d474d02eb349200dc4a831c8c93f05a2154c559f09b

COPY --from=go-build /deps/golang/bin/ /usr/local/bin/

COPY deps/rpm/ /tmp/rpm-installation/
RUN cd /tmp/rpm-installation && \
    ./install-rpms.sh && \
    rm -r /tmp/rpm-installation
