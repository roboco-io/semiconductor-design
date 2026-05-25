#!/usr/bin/env bash
# docker/build-metric-collector.sh
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
if [[ "${1:-}" == "--push" ]]; then
  : "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"
fi

rm -rf dist
uv build --wheel --out-dir dist

L1_SHA=$(uv run semi-run lockfile-verify --scope l1 | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="${IMAGE_NAME:-semi-design-${APP_ENV:-dev}-metric-collector}"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"

docker build \
  --provenance=false \
  -t "$LOCAL_TAG" \
  -f docker/metric-collector.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  .

SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "metric-collector image size: ${SIZE_MB} MB"

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
  echo "metric-collector ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"metric-collector\" = \"${DIGEST}\"" "$LOCKFILE"
fi
