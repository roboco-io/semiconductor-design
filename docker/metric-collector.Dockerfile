# syntax=docker/dockerfile:1.7
# docker/metric-collector.Dockerfile

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends awscli \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY dist/*.whl /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/*.whl

COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

LABEL org.opencontainers.image.title="semi/metric-collector" \
      org.opencontainers.image.description="Parses synth/sta/drc reports into Metrics JSON using semi_design_runner wheel (single-source parser)."

ENTRYPOINT ["/opt/bin/run-stage.sh"]
