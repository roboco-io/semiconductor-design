.PHONY: install test lint fmt clean graph-update graph-build graph-serve graph-lint freshness-inject kg-all kg-all-smoke run lockfile-verify

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests scripts

fmt:
	uv run ruff format src tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +

graph-update:
	uv run graphify update . && uv run python scripts/inject_freshness.py --graph graphify-out/graph.json

graph-build:
	@echo "Full graphify build must be run from an AI agent session."
	@echo "In Claude Code, invoke: /graphify ."
	@echo "Or follow skill.md recipe (see docs/superpowers/specs/2026-04-22-graphify-adoption-design.md §4.1)."
	@echo "After the AI session finishes the rebuild, run: make freshness-inject"

graph-serve:
	uv run python -m graphify.serve graphify-out/graph.json

graph-lint:
	uv run python scripts/graph_integrity_check.py graphify-out/graph.json

freshness-inject:
	uv run python scripts/inject_freshness.py --graph graphify-out/graph.json

# G1 kill-gate aggregator. Smoke mode runs offline with synthetic metrics;
# default mode requires BUCKET + STATE_MACHINE_ARN env (real AWS).
# Per overview §8 G1 exit criterion 7 — `make kg-all` must exit 0.
kg-all:
	bash scripts/kg/run-all.sh

kg-all-smoke:
	SMOKE=1 bash scripts/kg/run-all.sh

# Verify lockfile.yaml integrity (L1 scope) — wrapper for `semi-run lockfile-verify`.
# Required by docs/superpowers/plans/2026-05-10-g1-first-smoke.md §2.1 pre-flight.
# Exit 0 on pass, 1 on fail (CLI raises SystemExit(1) when result.verified == false).
lockfile-verify:
	uv run semi-run lockfile-verify --scope l1

# Submit one of the checked-in sample specs to the deployed Step Functions
# state machine. specs/<DESIGN>-<STACK>.yaml is treated as a template — the
# `run_id`, `l1_lockfile_sha`, and optionally `seed` fields are filled at
# submission time so checked-in samples never go stale against the lockfile.
#
# Usage:
#   make run DESIGN=gcd  STACK=orfs       BUCKET=... STATE_MACHINE_ARN=...
#   make run DESIGN=gcd  STACK=orfs SEED=1337  BUCKET=... STATE_MACHINE_ARN=...
#   make run DESIGN=gcd  STACK=librelane  BUCKET=... STATE_MACHINE_ARN=...
#   make run DESIGN=ibex STACK=orfs       BUCKET=... STATE_MACHINE_ARN=...   # post-G1: rejects
#   make run DESIGN=aes  STACK=orfs       BUCKET=... STATE_MACHINE_ARN=...   # post-G1: rejects
#
# Required: DESIGN, STACK, BUCKET, STATE_MACHINE_ARN
# Optional: SEED (default: spec yaml's existing `seed:` value preserved verbatim).
#   SEED= enables the G1 smoke seed-sweep pattern (plan §2.3): primary seed=42,
#   replay seed=42, distribution sanity seed=1337 / seed=31415. When SEED is
#   omitted, the spec's frozen `seed:` field is left untouched so the legacy
#   single-seed invocation remains byte-identical (reversible-patch invariant).
#   The RUN_ID embeds `-s<SEED>` only when SEED is provided, keeping the
#   default RUN_ID shape stable for existing callers.
run:
	@test -n "$(DESIGN)" || { echo "error: DESIGN= required (gcd|ibex|aes)"; exit 1; }
	@test -n "$(STACK)"  || { echo "error: STACK= required (orfs|librelane)";  exit 1; }
	@test -f "specs/$(DESIGN)-$(STACK).yaml" || { echo "error: specs/$(DESIGN)-$(STACK).yaml not found"; exit 1; }
	@test -n "$(BUCKET)" || { echo "error: BUCKET= required (S3 bucket name)"; exit 1; }
	@test -n "$(STATE_MACHINE_ARN)" || { echo "error: STATE_MACHINE_ARN= required"; exit 1; }
	@SEED_SUFFIX=$$(test -n "$(SEED)" && echo "-s$(SEED)" || echo ""); \
	 RUN_ID="$(DESIGN)-$(STACK)-$$(date +%s)$$SEED_SUFFIX"; \
	 L1_SHA=$$(uv run semi-run lockfile-verify --scope l1 | jq -r '.l1_lockfile_sha'); \
	 TMP_SPEC=$$(mktemp -t spec-XXXXXX.yaml); \
	 cp "specs/$(DESIGN)-$(STACK).yaml" "$$TMP_SPEC"; \
	 yq -i ".run_id = \"$$RUN_ID\" | .l1_lockfile_sha = \"$$L1_SHA\"" "$$TMP_SPEC"; \
	 if [ -n "$(SEED)" ]; then yq -i ".seed = $(SEED)" "$$TMP_SPEC"; fi; \
	 echo "Generated spec: $$TMP_SPEC (run_id=$$RUN_ID, l1_sha=$$L1_SHA, seed=$$(yq -r '.seed' "$$TMP_SPEC"))"; \
	 uv run semi-run init --spec "$$TMP_SPEC" --bucket $(BUCKET) && \
	 uv run semi-run submit --run-id "$$RUN_ID" --state-machine-arn $(STATE_MACHINE_ARN); \
	 rc=$$?; rm -f "$$TMP_SPEC"; exit $$rc
