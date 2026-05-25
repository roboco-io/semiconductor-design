#!/usr/bin/env bash
# docker/build-librelane.sh
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
if [[ "${1:-}" == "--push" ]]; then
  : "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"
fi

LIBRELANE_REF=$(yq -r '.commit_shas.librelane' "$LOCKFILE")
LIBRELANE_DIGEST=$(yq -r '.container_digests.librelane_base' "$LOCKFILE" | sed 's/^sha256://')
OPEN_PDKS_SHA=$(yq -r '.commit_shas.open_pdks' "$LOCKFILE")
L1_SHA=$(uv run semi-run lockfile-verify --scope l1 | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="${IMAGE_NAME:-semi-design-${APP_ENV:-dev}-librelane-runner}"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"

docker build \
  --provenance=false \
  -t "$LOCAL_TAG" \
  -f docker/librelane-runner.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  --build-arg "LIBRELANE_DIGEST=${LIBRELANE_DIGEST}" \
  --build-arg "LIBRELANE_REF=${LIBRELANE_REF}" \
  --build-arg "OPEN_PDKS_SHA=${OPEN_PDKS_SHA}" \
  .

SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "librelane-runner image size: ${SIZE_MB} MB"

if [[ "${1:-}" == "--push" ]]; then
  REMOTE_TAG="${ECR_REGISTRY}/${IMAGE_NAME}:${L1_SHA}"
  aws ecr get-login-password --region "$(echo "$ECR_REGISTRY" | cut -d. -f4)" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker tag "$LOCAL_TAG" "$REMOTE_TAG"
  docker push "$REMOTE_TAG"

  DIGEST=$(aws ecr describe-images \
    --repository-name "$IMAGE_NAME" \
    --image-ids "imageTag=${L1_SHA}" \
    --query 'imageDetails[0].imageDigest' --output text)
  echo "librelane-runner ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"librelane-runner\" = \"${DIGEST}\"" "$LOCKFILE"
fi
