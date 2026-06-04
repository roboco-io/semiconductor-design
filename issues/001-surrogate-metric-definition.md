---
id: 001
title: surrogate 지표 정의 (slack/area/routability, 단일 vs 복합)
status: open
type: decision
blocks: [FR-1, FR-3, "PRD §9 임계값", 002, 003, 004, 005]
related_prd: OD-1
related_intent: "What §엣지케이스 (복수 지표 단일화)"
---

# 001 — surrogate 지표 정의

## 배경

루프는 단일 val 지표를 최소화/최대화해 winner를 고른다 (FR-3·FR-4, AutoResearch `val_bpb` 계승). 그러나 EDA surrogate가 예측할 *대상 지표*가 미정이다. INTENT `What` 엣지케이스는 "slack vs area vs routability 복수일 때 단일화 방법"을 (?)로 둔다. 이 결정이 feature(002)·라벨 규모(003)·모델(004)·임계값(005)을 모두 선행한다.

## 옵션

- **A. routability** — CircuitNet/RouteNet 계열. 조기 DRV 예측, classification/heatmap.
- **B. timing slack** — STA worst slack 회귀. label 추출이 명확(`*.rpt`).
- **C. area** — 합성/배치 후 면적 회귀. 가장 단순한 label.
- **D. 복합** — 다지표 → 가중합 또는 Pareto. 단일 지표 최소화 제약(NFR-1 계승)과 충돌 가능.

## 결정 기준

- flow 1회 실행으로 label 추출이 명확한가 (FR-1, 003과 연동).
- 단일 스칼라로 환원 가능한가 (selection이 단일 지표 전제).
- 사람-수작업 baseline이 존재해 비교 가능한가 (H-A, 005).

## 액션 아이템

- [ ] 후보 지표 1개 선택(또는 복합 단일화 규칙 확정) → 설계 spec에 기록.
- [ ] 선택 지표의 `*.rpt` 추출 경로 확인 (오픈소스 flow 기준).
- [ ] 002·003·004·005 잠금 해제.
