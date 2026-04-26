#!/usr/bin/env bash
# KG-D: Deterministic Spot reclaim via container env SIMULATE_SPOT_RECLAIM=1
# → exit 143 (= 128 + SIGTERM). SFN retry(MaxAttempts=2, BackoffRate=2) must
# recover ≥80% of 10 simulated jobs.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"
TOTAL="${SMOKE_TOTAL:-10}"

if [[ "$MODE" == "smoke" ]]; then
    REC="${SMOKE_RECOVERED:-8}"
    RATE=$(echo "scale=2; $REC / $TOTAL" | bc)
    PASS="false"; (( $(echo "$RATE >= 0.80" | bc -l) )) && PASS="true"
    jq -n --argjson passed "$PASS" --argjson r "$REC" --argjson t "$TOTAL" --argjson rate "$RATE" \
      '{passed: $passed, recovered: $r, total: $t, recovery_rate: $rate, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${BUCKET:?}" "${STATE_MACHINE_ARN:?}"
REC=0
for i in $(seq 1 "$TOTAL"); do
    RUN_ID=$(uv run python -c "import ulid; print(ulid.new())")
    uv run semi-run init --spec specs/gcd-orfs.yaml --bucket "$BUCKET" --simulate-spot-reclaim > /tmp/kg-d.$i.json
    EXEC=$(uv run semi-run submit --run-id "$RUN_ID" --state-machine-arn "$STATE_MACHINE_ARN")
    STATUS=$(uv run semi-run status --run-id "$RUN_ID" --execution-arn "$EXEC" --wait)
    echo "$STATUS" | jq -e '.ddb_status == "clean"' >/dev/null && REC=$((REC+1))
done
RATE=$(echo "scale=2; $REC / $TOTAL" | bc)
PASS="false"; (( $(echo "$RATE >= 0.80" | bc -l) )) && PASS="true"
jq -n --argjson passed "$PASS" --argjson r "$REC" --argjson t "$TOTAL" --argjson rate "$RATE" \
  '{passed: $passed, recovered: $r, total: $t, recovery_rate: $rate, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
