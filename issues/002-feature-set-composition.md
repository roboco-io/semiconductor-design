---
id: 002
title: feature_set 구성 (합성 리포트 어느 필드까지)
status: open
type: decision
blocks: [FR-1]
related_prd: OD-2
related_intent: "What §핵심기능 1 (feature = 합성 직후)"
depends_on: [001]
---

# 002 — feature_set 구성

> **OD-1 확정 (001 resolved, 2026-06-04)**: 지표 = per-path timing slack 회귀. feature는 **path 단위 합성 feature**로 한정된다. 아래 옵션 A(스칼라)가 기본선, critical-path 쏠림 대응(informative sampling)이 신규 과제.

## 배경

`prepare.py`(frozen, NFR-2)는 합성 직후 feature를 추출해 `DATASET.feature_set`에 고정한다 (FR-1). 어느 필드까지 feature로 쓸지 미정 — 너무 적으면 예측력 부족, 너무 많으면 누수/과적합 위험(INTENT 엣지케이스 "val 지표만 좋은 경우"). 001 확정으로 feature 단위는 **timing path**, label은 post-route slack으로 고정됐다.

## 옵션

- **A. 합성 리포트 스칼라만** — cell count, area, fanout, net 수 등 집계 통계. tabular(004-A)와 정합.
- **B. + 그래프 구조** — netlist를 그래프로, node/edge feature. GNN(004-B) 전제.
- **C. + 배치 전 추정치** — congestion map 등. routability(001-A)에 유리하나 추출 비용↑.

## 결정 기준

- 001 지표와의 인과 관련성 (예: routability ← congestion, area ← cell count).
- frozen 후 변경 불가 — 보수적으로 충분히 포함하되 누수 필드 배제.
- 004 모델 클래스와 호환 (tabular면 스칼라, GNN이면 구조).

## 액션 아이템

- [ ] 001 확정 후 feature 후보 목록 작성.
- [ ] 누수 위험 필드(라벨에서 역산 가능한 것) 배제 규칙 정의.
- [ ] `prepare.py` feature 추출 스펙 freeze.
