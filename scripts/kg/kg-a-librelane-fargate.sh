#!/usr/bin/env bash
# KG-A: LibreLane 3.0.2 on Fargate Spot — gcd within 30min, ephemeral <21GB,
# image pull <10min. Smoke mode runs offline with synthetic metrics; live mode
# requires BUCKET + STATE_MACHINE_ARN env and consumes real AWS resources.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    EPH="${SMOKE_EPHEMERAL_GB:-12.3}"
    PULL="${SMOKE_PULL_SEC:-420}"
    DUR="${SMOKE_DURATION:-1200}"
    PASS="true"
    (( $(echo "$EPH > 21" | bc -l) )) && PASS="false"
    [[ "$PULL" -gt 600 ]] && PASS="false"
    [[ "$DUR" -gt 1800 ]] && PASS="false"
    jq -n --argjson passed "$PASS" --argjson e "$EPH" --argjson p "$PULL" --argjson d "$DUR" \
      '{passed: $passed, ephemeral_peak_gb: $e, image_pull_seconds: $p, duration_seconds: $d, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${BUCKET:?}" "${STATE_MACHINE_ARN:?}"
START=$(date +%s)
RUN_ID=$(uv run python -c "import ulid; print(ulid.new())")
uv run semi-run init --spec specs/gcd-librelane.yaml --bucket "$BUCKET" > /tmp/kg-a-init.json
EXEC=$(uv run semi-run submit --run-id "$RUN_ID" --state-machine-arn "$STATE_MACHINE_ARN")
uv run semi-run status --run-id "$RUN_ID" --execution-arn "$EXEC"
END=$(date +%s); DUR=$((END-START))
EPH=$(aws logs filter-log-events --log-group-name /aws/fargate/semi-design \
  --filter-pattern ephemeral_peak --limit 1 --query 'events[0].message' --output text \
  | jq -r '.peak_gb // 0')
PULL=$(aws logs filter-log-events --log-group-name /aws/fargate/semi-design \
  --filter-pattern image_pull --limit 1 --query 'events[0].message' --output text \
  | jq -r '.seconds // 0')
PASS="true"
(( $(echo "$EPH > 21" | bc -l) )) && PASS="false"
[[ "$PULL" -gt 600 ]] && PASS="false"
[[ "$DUR" -gt 1800 ]] && PASS="false"
jq -n --argjson passed "$PASS" --argjson e "$EPH" --argjson p "$PULL" --argjson d "$DUR" \
  '{passed: $passed, ephemeral_peak_gb: $e, image_pull_seconds: $p, duration_seconds: $d, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
