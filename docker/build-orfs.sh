#!/usr/bin/env bash
# docker/build-orfs.sh
#
# Deterministic build wrapper. Reads SHAs from lockfile.yaml via yq and builds
# semi/orfs-runner tagged by the short l1_lockfile_sha so ECR tags are
# immutable and content-addressable.
#
# Usage:  docker/build-orfs.sh [--push]
#
# Env:
#   ECR_REGISTRY   e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com
#   LOCKFILE       defaults to ./lockfile.yaml
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
if [[ "${1:-}" == "--push" ]]; then
  : "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"
fi

OPENROAD_SHA=$(yq -r '.commit_shas.openroad'  "$LOCKFILE")
YOSYS_TAG=$(yq    -r '.commit_shas.yosys'     "$LOCKFILE")
OPEN_PDKS_SHA=$(yq -r '.commit_shas.open_pdks' "$LOCKFILE")
L1_SHA=$(uv run semi-run lockfile-verify --scope l1 | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="${IMAGE_NAME:-semi-design-${APP_ENV:-dev}-orfs-runner}"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"

docker build \
  --provenance=false \
  --sbom=false \
  -t "$LOCAL_TAG" \
  -f docker/orfs-runner.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  --build-arg "OPENROAD_SHA=${OPENROAD_SHA}" \
  --build-arg "YOSYS_TAG=${YOSYS_TAG}" \
  --build-arg "OPEN_PDKS_SHA=${OPEN_PDKS_SHA}" \
  .

# Measure image size (spec §5 expected ~2.5GB).
SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "orfs-runner image size: ${SIZE_MB} MB"

if [[ "${1:-}" == "--push" ]]; then
  REMOTE_TAG="${ECR_REGISTRY}/${IMAGE_NAME}:${L1_SHA}"
  REGION=$(echo "$ECR_REGISTRY" | cut -d. -f4)
  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker tag "$LOCAL_TAG" "$REMOTE_TAG"
  docker push "$REMOTE_TAG"

  # Capture the ECR-assigned content digest back into lockfile.yaml.
  DIGEST=$(aws ecr describe-images \
    --repository-name "$IMAGE_NAME" \
    --image-ids "imageTag=${L1_SHA}" \
    --region "$REGION" \
    --query 'imageDetails[0].imageDigest' --output text)
  echo "orfs-runner ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"orfs-runner\" = \"${DIGEST}\"" "$LOCKFILE"
fi
