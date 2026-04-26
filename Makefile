.PHONY: install test lint fmt clean graph-update graph-build graph-serve graph-lint freshness-inject kg-all kg-all-smoke

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
