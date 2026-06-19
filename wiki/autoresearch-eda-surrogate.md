---
title: AutoResearch EDA Surrogate
aliases: [autoresearch-eda-surrogate, surrogate pivot]
type: concept
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[evolution-loop]], [[gate-chain]], [[adr-operator-empowerment-repivot]]
---

# AutoResearch EDA Surrogate

> Karpathy AutoResearch의 population-based evolution 루프를 **EDA surrogate 지표예측 모델**
> (합성 직후 feature → 최종 PPA/timing 예측) 학습에 적용하는 프로젝트(2026-05-29 피벗).

## 배경
전체 EDA 3-layer 통합 프로그램이 Operator 1명에 과도하다는 판단으로 축소 피벗. 구 3-layer 자산은
`archive/integrated-program-3layer` 브랜치에 무손실 보존. main은 serverless-autoresearch 정렬 골격.

## 핵심 내용
- 에이전트(Claude+Codex CLI)는 **`train.py` 단일 파일만** 변형([[frozen-contract]]).
- 고정 예산 학습 후 단일 val 지표(`val_mae`)로 keep/discard, **객관적 자동 게이트**가 승격 판정([[gate-chain]]).
- 4-step 루프: candidate_gen → batch_launch → result_collection → selection([[evolution-loop]]).
- novelty 축은 절대 PPA가 아니라 **비전문가 empowerment + 큰 흐름의 이해가능성**([[adr-operator-empowerment-repivot]]).

## 주의사항 / 오해
- parameter sweep 단독(ORFS-agent 영역)이 아니라 **surrogate 모델 학습의 자동 연구**다.
- 구독 CLI(claude/codex)로만 LLM 호출 — metered LLM API 비용 없음. 실 $ 비용은 AWS뿐.

## 참고
- `INTENT.md` (Why/What/Not/Learnings), `PRD.md` (4-엔티티 ERD).
