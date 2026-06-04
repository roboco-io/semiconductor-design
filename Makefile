.PHONY: install test lint fmt clean prepare

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

clean:
	rm -rf .pytest_cache .ruff_cache .coverage dist build **/__pycache__

prepare:
	uv run python prepare.py --synth $(SYNTH) --route $(ROUTE) --lockfile $(LOCKFILE) --design-id $(DESIGN) --out-dir $(OUT)

# NOTE: 피벗 직후 skeleton. AutoResearch 루프 타깃(prepare/train/generate/launch/collect/select)은
# 구현 plan 승인 후 serverless-autoresearch 구조에 맞춰 추가한다.
