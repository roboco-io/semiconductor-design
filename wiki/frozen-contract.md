---
title: Frozen Contract
aliases: [frozen-contract, train.py 계약]
type: policy
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[evolution-loop]], [[autoresearch-eda-surrogate]]
---

# Frozen Contract — 공정 비교를 위한 변형 계약

## 목적
에이전트가 `train.py`만 자유 변형하되, 공정 비교와 평가 무결성을 깨지 않도록 불변 경계를 강제한다.

## 규칙
- [ ] **단일 파일**: `train.py`만 변형. `prepare.py`·`src/prepare_lib/`·커밋된 dataset.jsonl은 read-only(frozen).
- [ ] **신규 의존성 금지**: `sklearn`, `numpy`, `joblib`, `click`, stdlib만 import. GPU·딥러닝 금지.
- [ ] **출력 계약**: stdout에 `{"val_mae": <float>}` 한 줄, `--out <dir>/model.joblib` 저장.
- [ ] **시그니처 불변**: CLI `--data`/`--out`/`--seed`, 8 `FEATURE_NAMES` 불변.
- [ ] **고정 CPU 예산**(분 단위).

## 적용 범위
- 대상: candidate_gen이 만드는 모든 후보([[evolution-loop]]).
- 제외: orchestrator·게이트·리포트 코드(Operator 소유 substrate).

## 위반 시 대응
- **탐지**: 학습 실패 시 `val_mae=inf`로 자연 도태. 계약 우회(gaming)는 [[codex-review-gate]]가 차단.
- **harness 견고성**: 에이전트가 소스 대신 산문을 반환하면 `_extract_code`/`_looks_like_source`가
  감지해 baseline fallback(gen-004 cand-002 회귀). 가드 미통과 시 후보를 버리지 않고 baseline 채점.

## 미해결 이슈
- `_looks_like_source` 휴리스틱 강도(오탈락 vs 누락 균형)는 진행 중 — [[generation-log]] gen-004 후속.
