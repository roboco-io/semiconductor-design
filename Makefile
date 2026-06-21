.PHONY: install test lint fmt clean prepare train loop

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests prepare.py train.py

fmt:
	uv run ruff format src tests prepare.py train.py

clean:
	rm -rf .pytest_cache .ruff_cache .coverage dist build **/__pycache__

prepare:
	uv run python prepare.py --synth $(SYNTH) --route $(ROUTE) --lockfile $(LOCKFILE) --design-id $(DESIGN) --out-dir $(OUT)

DATA ?= dataset.jsonl
SEED ?= 0

train:
	uv run python train.py --data $(DATA) --out $(OUT) --seed $(SEED)

# NOTE: 피벗 직후 skeleton. AutoResearch 루프 타깃(prepare/train/generate/launch/collect/select)은
# 구현 plan 승인 후 serverless-autoresearch 구조에 맞춰 추가한다.

GEN ?= 1
# gen-008+ 루프 dataset: 4설계 혼합(gcd+aes+ibex+jpeg, Sub-A 2026-06-21). LODO/T1 4 fold로
# 통계력↑. gen-001~007 val_mae와 직접 비교 금지(설계 교체).
DATASET ?= experiments/multidesign/dataset-4design.jsonl
N ?= 4
PROGRAM ?= program.md

loop:
	uv run python src/pipeline/orchestrator.py --gen $(GEN) --dataset $(DATASET) --n $(N) --program $(PROGRAM)
