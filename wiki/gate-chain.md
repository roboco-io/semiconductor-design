---
title: Gate Chain
aliases: [gate-chain, promotion gate, separation of powers]
type: concept
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[evolution-loop]], [[adr-multiseed-median-selection]], [[cross-design-generalization]], [[codex-review-gate]]
---

# Gate Chain — 4단 권력분립 승격 게이트

> winner 승격은 사람이 아니라 **생성자 ≠ 판정자** 원칙의 객관적 게이트 체인이 판정한다.

## 배경
gen-002 위양성(단일 seed로 broken winner가 승격될 뻔)을 계기로, "주장의 신뢰성"을 자동으로
보장하는 게이트가 자율성의 *전제조건*이 됐다. 사람을 per-winner 결정에서 빼려면 엄밀 게이트가 필요.

## 핵심 내용 (체인 순서)
1. **median** — 5-seed median val_mae로 winner 선발([[adr-multiseed-median-selection]]). 통계 노이즈 차단.
2. **LODO** — held-out 설계 일반화 probe. baseline 후퇴(`worse`)·부분 fold 실패 시 `rejected_lodo`로
   차단(T1·Codex 생략, fail-fast). [[cross-design-generalization]] 참조.
3. **T1** — winner vs baseline 통계 검정(`distinguishable`/`worse`). 다설계 dataset에선 **교차설계
   repeated-LODO**(D×R fold, 설계 단위 held-out)로 LODO와 같은 축을 통계 검정(2026-06-21 재정의);
   단일설계에선 기존 혼합 K-fold. gen-006 winner가 혼합-T1 `worse` → 교차설계-T1 `distinguishable`로
   반전 — 두 스킴이 다른 축(robustness↔accuracy)을 측정함을 입증.
4. **Codex** — 무결성·안전·gaming 심사. T1이 못 잡는 계약 우회를 차단([[codex-review-gate]]).

## 주의사항 / 오해
- **LODO 부분실패 차단은 orchestrator 층에서 강제**한다 — `run_crossdesign_gate`(probe 함수)는
  부분실패에 통과 verdict를 낼 수 있으므로, 호출자가 `n_valid < n_designs → 차단`을 명시.
- 단일 설계 dataset이면 LODO 생략(≥2 설계 필요), 리포트에 생략 사실 명기.
- 사전 고정 판정: 게이트/임계값은 결과를 보기 전에 고정한다.

## 참고
- `src/pipeline/orchestrator.py:run_generation`, `validation.py`.
