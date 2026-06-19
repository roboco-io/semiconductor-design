---
title: ADR Operator Empowerment Re-pivot
aliases: [adr-operator-empowerment-repivot, empowerment pivot]
type: decision
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[autoresearch-eda-surrogate]], [[gate-chain]]
---

# ADR: Operator authority → 비전문가 empowerment

- **일자**: 2026-06-08
- **상태**: Accepted (status clarified → exploring)

## 맥락
"수동 승인(H-B)을 핵심으로 꼽는 프레이밍이 과했다"는 판단. Karpathy식 자율 진행이 기본이어야 하고
사람은 방향·큰 흐름만 이해·조종해야 한다. 목표는 비전문가가 전문영역서 의미있는 성과를 내는 것.

## 결정
- **novelty 축 이동**: "자율 무인 vs Operator authority"(거버넌스) → **"비전문가 empowerment +
  큰 흐름의 이해가능성"**(접근성).
- INTENT Not의 "자율 무인 머지 절대 금지" → **"맹목적 자율 금지(객관적 게이트+이해가능성이 조건)"**.
- H-B 재정의: per-winner 승인 없이 방향·이해만으로 신뢰가능한 자율.

## 대안
- A안(채택): 게이트로 신뢰 보장 + 사람은 방향타·학습자.
- B안(기각): per-winner 사람 승인 유지 — Karpathy 자율성과 충돌, 비전문가 empowerment 약화.

## 결과
- 직전에 만든 T1 게이트가 버려지지 않고 *격상* — advisory에서 자율 승격을 신뢰가능케 하는 자동 판정자로.
  엄밀 게이트가 있어야 사람을 per-winner 결정에서 뺄 수 있으므로([[gate-chain]]).
- status가 clarified → exploring으로 되돌아간 것 자체가 co-evolution 신호.

## 참고
- `INTENT.md` Learnings 2026-06-08.
