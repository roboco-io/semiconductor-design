# syntax=docker/dockerfile:1.7
# docker/librelane-runner.Dockerfile

ARG LIBRELANE_REF

FROM ghcr.io/librelane/librelane:${LIBRELANE_REF} AS librelane-base

ARG OPEN_PDKS_SHA
ARG LIBRELANE_REF

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PDK_ROOT=/opt/pdk \
    LIBRELANE_REF=${LIBRELANE_REF}

USER root

RUN nix-env -iA nixpkgs.awscli2 nixpkgs.bash nixpkgs.coreutils

RUN mkdir -p /opt/pdk && \
    nix-build --no-out-link \
      --arg openPdksRev "\"${OPEN_PDKS_SHA}\"" \
      '<nixpkgs>' -A open_pdks && \
    cp -r $(nix-store -q --outputs $(nix-store -qR $(which librelane) | grep open_pdks))/share/pdk/sky130A /opt/pdk/sky130A

COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

LABEL org.opencontainers.image.title="semi/librelane-runner" \
      org.opencontainers.image.description="LibreLane 2.4 (FOSSi Nix base) + sky130A, SHA-pinned." \
      org.opencontainers.image.version="${LIBRELANE_REF}"

ENTRYPOINT ["/opt/bin/run-stage.sh"]
