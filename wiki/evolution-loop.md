---
title: Evolution Loop
aliases: [evolution-loop, 4-step loop, orchestrator]
type: entity
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[autoresearch-eda-surrogate]], [[gate-chain]], [[generation-log]]
---

# Evolution Loop — 세대별 진화 파이프라인

## 책임
한 세대(generation)에서 후보를 생성·학습·선발하고 게이트로 승격을 판정한다.

## 인터페이스
- 진입: `make loop GEN=N` 또는 `orchestrator.py --gen N --dataset D --n N --auto`.
- `--auto` 플래그가 **게이트 체인을 켠다**. 없으면 `awaiting_operator`로 멈춤(수동 검토).

## 내부 구조 (4-step)
1. **candidate_gen** — baseline `train.py`를 N개 변형. SDK는 `SDKS[i%2]`로 claude/codex 교대,
   전략은 conservative/moderate/aggressive 순환.
2. **runner (batch_launch)** — 후보×seed(기본 0~4) 학습, `val_mae` 산출.
3. **selection** — 5-seed **median**으로 winner 선발([[adr-multiseed-median-selection]]).
4. **gate** — median → LODO → T1 → Codex 통과 시 자동 승격([[gate-chain]]).

## 의존
- `src/pipeline/sdk.py` — 실제 CLI 호출. `_extract_code`/`_looks_like_source`가 산문 반환을 baseline fallback.
- `src/pipeline/validation.py` — `run_crossdesign_gate`(LODO), `run_validation_gate`(T1).
- `src/pipeline/promotion_reviewer.py` — Codex 승격 심사.

## 코드 위치
- `src/pipeline/orchestrator.py`, `candidate_gen.py`, `runner.py`, `selection.py`, `report.py`.
