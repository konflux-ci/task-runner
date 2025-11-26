FROM registry.access.redhat.com/ubi10/go-toolset:1.25@sha256:182645783ad0a0af4a78d928f2d9167815d59c12cc156aa3c229cf3a49d636d9 AS go-build

USER 0

WORKDIR /deps/golang/src

COPY deps/golang/go.mod deps/golang/go.sum .
RUN go mod download

COPY deps/golang/install-tools.sh .
RUN GOBIN=/deps/golang/bin ./install-tools.sh


FROM registry.access.redhat.com/ubi10/ubi-minimal:10.1@sha256:28ec2f4662bdc4b0d4893ef0d8aebf36a5165dfb1d1dc9f46319bd8a03ed3365

RUN microdnf -y --setopt install_weak_deps=0 reinstall \
        bash \
        coreutils-single \
        curl \
        findutils \
        gawk \
        grep \
        microdnf \
        rpm \
        sed && \
    microdnf clean all

COPY --from=go-build /deps/golang/bin/ /usr/local/bin/
