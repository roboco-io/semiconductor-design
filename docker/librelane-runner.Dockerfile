# syntax=docker/dockerfile:1.7
# docker/librelane-runner.Dockerfile

ARG LIBRELANE_DIGEST

FROM ghcr.io/librelane/librelane@sha256:${LIBRELANE_DIGEST} AS librelane-base

ARG OPEN_PDKS_SHA
ARG LIBRELANE_REF

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PDK_ROOT=/opt/pdk \
    LIBRELANE_REF=${LIBRELANE_REF}

USER root

RUN nix-env -iA nixpkgs.awscli2 nixpkgs.bash nixpkgs.coreutils

RUN mkdir -p /opt/pdk && \
    OPEN_PDKS_OUT=$(nix-build --no-out-link \
      --arg openPdksRev "\"${OPEN_PDKS_SHA}\"" '<nixpkgs>' -A open_pdks) && \
    test -d "${OPEN_PDKS_OUT}/share/pdk/sky130A" && \
    cp -r "${OPEN_PDKS_OUT}/share/pdk/sky130A" /opt/pdk/sky130A

COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

# Spec §11 G1 boundary: Verilator is excluded. Assert absence.
RUN ! command -v verilator

LABEL org.opencontainers.image.title="semi/librelane-runner" \
      org.opencontainers.image.description="LibreLane 3.0.2 (FOSSi Nix base) + sky130A, SHA-pinned." \
      org.opencontainers.image.version="${LIBRELANE_REF}"

ENTRYPOINT ["/opt/bin/run-stage.sh"]
