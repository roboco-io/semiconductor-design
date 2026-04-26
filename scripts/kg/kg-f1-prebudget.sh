#!/usr/bin/env bash
# KG-F1: Prove pre-RunTask budget guard rejects BEFORE any ECS call.
# Spec with budget=0.01 + planned sum=5.0 must be rejected by `semi-run init`.
# Smoke mode validates Spec.cost.check_planned_budget without invoking AWS.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"
SPEC=specs/_kg_f1_overbudget.yaml

mkdir -p specs
cat > "$SPEC" <<EOF
version: 1
run_id: "kg-f1-$(date +%s)"
design: gcd
stack: orfs
flow_parameters: {}
compute_budget_usd: 0.01
planned_cost_per_stage_usd:
  synth: 2.5
  pnr: 2.5
seed: 0
l1_lockfile_sha: "sha256:0000000000000000000000000000000000000000000000000000000000000000"
EOF

if [[ "$MODE" == "smoke" ]]; then
    REASON=$(uv run python -c "
from semi_design_runner.schemas import Spec
from semi_design_runner.cost import check_planned_budget, BudgetExceededError
import yaml
s = Spec.model_validate(yaml.safe_load(open('$SPEC')))
try: check_planned_budget(s); print('')
except BudgetExceededError as e: print(str(e))
")
    if [[ -n "$REASON" ]]; then
        jq -n --arg r "$REASON" '{passed: true, rejected: true, reason: "planned_cost_exceeds_budget", detail: $r, ecs_runs: 0, mode: "smoke"}'
        exit 0
    fi
    jq -n '{passed: false, rejected: false, ecs_runs: 0, mode: "smoke"}'; exit 1
fi

uv run semi-run init --spec "$SPEC" --bucket "${BUCKET:?}" > /tmp/kg-f1.json && {
    jq -n '{passed: false, rejected: false, reason: "init accepted overbudget spec", mode: "live"}'; exit 1;
} || true
jq -n '{passed: true, rejected: true, reason: "planned_cost_exceeds_budget", ecs_runs: 0, mode: "live"}'
