#!/usr/bin/env bash
# run-all.sh: Aggregate KG gates and emit a single JSON report.
# G1-mandatory gates: KG-A, KG-D, KG-E, KG-F1. (KG-B, KG-C2 optional.)
# Honors $SMOKE — when set, every script short-circuits to synthetic metrics.
#
# Exit codes:
#   0 — every G1-mandatory gate passed
#   1 — any G1-mandatory gate failed (per-gate JSON in stdout, summary in stderr)
set -uo pipefail

KG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATES=(
    "kg-a:kg-a-librelane-fargate.sh"
    "kg-d:kg-d-spot-reclaim.sh"
    "kg-e:kg-e-ddb-write-amp.sh"
    "kg-f1:kg-f1-prebudget.sh"
)

REPORT="{}"
FAIL=0
for entry in "${GATES[@]}"; do
    GATE="${entry%%:*}"
    SCRIPT="${entry##*:}"
    if [[ ! -x "$KG_DIR/$SCRIPT" ]]; then
        REPORT=$(jq --arg g "$GATE" '. + {($g): {passed: false, error: "script missing or not executable"}}' <<<"$REPORT")
        FAIL=1
        continue
    fi
    OUT=$(bash "$KG_DIR/$SCRIPT" 2>/dev/null) || RC=$? && RC=${RC:-0}
    if [[ -z "$OUT" ]]; then
        REPORT=$(jq --arg g "$GATE" '. + {($g): {passed: false, error: "no output"}}' <<<"$REPORT")
        FAIL=1
        continue
    fi
    REPORT=$(jq --arg g "$GATE" --argjson r "$OUT" '. + {($g): $r}' <<<"$REPORT")
    if ! jq -e --arg g "$GATE" '.[$g].passed == true' <<<"$REPORT" >/dev/null; then
        FAIL=1
    fi
done

ALL_PASS="true"; [[ "$FAIL" -ne 0 ]] && ALL_PASS="false"
jq --argjson all "$ALL_PASS" '. + {all_passed: $all, gates_run: ["kg-a", "kg-d", "kg-e", "kg-f1"]}' <<<"$REPORT"
exit "$FAIL"
