# syntax=docker/dockerfile:1.7
# docker/orfs-runner.Dockerfile
#
# Spec §5 semi/orfs-runner:
#   - debian:12-slim base
#   - ORFS + OpenROAD (pinned to lockfile.yaml.commit_shas.openroad)
#   - Yosys built from source at YosysHQ/yosys tag (lockfile.yaml.commit_shas.yosys, e.g. yosys-0.55)
#   - open_pdks sky130A (lockfile.yaml.commit_shas.open_pdks)
#   - NO Verilator (Codex review #8 — G1 has no functional simulation)
#
# ARGs are wired from `yq '.commit_shas.<key>' lockfile.yaml` in docker/build-orfs.sh.
# ENTRYPOINT delegates to the shared run-stage.sh wrapper so every L1 image
# follows the same env-var contract (spec §5: RUN_ID, STAGE, INPUT_S3_URI,
# OUTPUT_S3_URI, SIMULATE_SPOT_RECLAIM).

FROM debian:12-slim AS base

ARG OPENROAD_SHA
ARG YOSYS_TAG
ARG OPEN_PDKS_SHA

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PDK_ROOT=/opt/pdk \
    PATH=/opt/tools/openroad/bin:/opt/tools/yosys/bin:/usr/local/bin:/usr/bin:/bin

# Bootstrap layer — just enough to git-clone ORFS and let its own
# DependencyInstaller handle the version-sensitive bits (SWIG ≥ 4.3,
# libfmt, libspdlog, libeigen3, etc.) that Debian 12's apt cannot
# satisfy with hand-picked packages. awscli stays here because
# entrypoints/run-stage.sh uses it for S3 sync.
RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates curl wget unzip sudo \
      build-essential cmake python3 lsb-release \
      awscli \
 && rm -rf /var/lib/apt/lists/*

# --- OpenROAD / ORFS (pinned by SHA) ---------------------------------------
# DependencyInstaller is the canonical OpenROAD entry point for system deps.
# Hand-picked apt lists drift against upstream's CMake findpackage version
# checks (cmake ≥ 3.20, swig ≥ 4.3, libfmt ≥ 8.x, etc.). The installer is
# pinned to the same SHA we check out, so its package set evolves with
# OpenROAD and stays in sync with build_openroad.sh's expectations.
RUN mkdir -p /opt/src && cd /opt/src \
 && git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git orfs \
 && cd orfs \
 && git checkout "${OPENROAD_SHA}" \
 && ./tools/OpenROAD/etc/DependencyInstaller.sh -base -common \
 && ./build_openroad.sh --local --threads "$(nproc)" \
 && mv tools/OpenROAD/build /opt/tools/openroad \
 && ln -s /opt/src/orfs /opt/tools/orfs

# --- Yosys (built from source at YosysHQ/yosys tag) ------------------------
# Previous attempt used oss-cad-suite-build prebuilts, but that repo uses
# date tags (YYYY-MM-DD), not `yosys-N.NN`. Source build keeps the lockfile
# key stable (`commit_shas.yosys: yosys-0.55`) and matches upstream tagging.
RUN mkdir -p /opt/src/yosys && cd /opt/src/yosys \
 && git clone --recurse-submodules https://github.com/YosysHQ/yosys.git . \
 && git checkout "${YOSYS_TAG}" \
 && git submodule update --init --recursive \
 && make config-clang \
 && make -j"$(nproc)" PREFIX=/opt/tools/yosys \
 && make install PREFIX=/opt/tools/yosys \
 && rm -rf /opt/src/yosys/.git

# --- open_pdks sky130A (pinned) --------------------------------------------
RUN mkdir -p /opt/src/open_pdks && cd /opt/src/open_pdks \
 && git clone https://github.com/RTimothyEdwards/open_pdks.git . \
 && git checkout "${OPEN_PDKS_SHA}" \
 && ./configure --enable-sky130-pdk --prefix="${PDK_ROOT}" \
 && make -j"$(nproc)" && make install \
 && rm -rf /opt/src/open_pdks/.git

# --- Shared ENTRYPOINT contract --------------------------------------------
COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

# Explicit negative assertion — Verilator is deliberately absent.
# Tests/docker/test_orfs_runner.py::test_orfs_runner_has_no_verilator asserts this.
# L3 (simulate activation) adds a separate semi/sim-runner image; do NOT add verilator here.
RUN ! command -v verilator

LABEL org.opencontainers.image.title="semi/orfs-runner" \
      org.opencontainers.image.description="ORFS + OpenROAD + Yosys + sky130A, SHA-pinned. No Verilator (G1)."

ENTRYPOINT ["/opt/bin/run-stage.sh"]
