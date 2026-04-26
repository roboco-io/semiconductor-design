#!/usr/bin/env bash
# KG-E: per-candidate Candidates.ddb_write_count < 50 (app-level counter,
# not CloudWatch). Smoke mode short-circuits on $SMOKE_COUNT; live mode reads
# the DynamoDB counter via semi_design_runner.aws.ddb.get_ddb_write_count.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    CNT="${SMOKE_COUNT:-12}"
    PASS="false"; [[ "$CNT" -lt 50 ]] && PASS="true"
    jq -n --argjson passed "$PASS" --argjson c "$CNT" \
      '{passed: $passed, ddb_write_count: $c, limit: 50, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${RUN_ID:?}"
CNT=$(uv run python -c "
from semi_design_runner.aws.clients import make_client
from semi_design_runner.aws.ddb import get_ddb_write_count
print(get_ddb_write_count(make_client('dynamodb'), table='Candidates', run_id='$RUN_ID', gen=0, cand=0))
")
PASS="false"; [[ "$CNT" -lt 50 ]] && PASS="true"
jq -n --argjson passed "$PASS" --argjson c "$CNT" \
  '{passed: $passed, ddb_write_count: $c, limit: 50, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
