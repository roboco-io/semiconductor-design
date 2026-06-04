---
id: 001
title: surrogate 지표 정의 (slack/area/routability, 단일 vs 복합)
status: resolved
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

- [x] 후보 지표 1개 선택 → 본 Resolution 기록.
- [x] 선택 지표의 `*.rpt` 추출 경로 확인 (OpenSTA `report_checks`).
- [x] 002·003·004·005 잠금 해제 (각 issue에 OD-1 제약 반영).

## Resolution (2026-06-04, brainstorming 승인)

**결정: per-path timing slack 회귀.** post-synthesis path feature → post-route path slack(ns) 예측.

판단 경로 (clarifying 3문항):
1. 지표는 novelty 축이 아니라 **루프 시연의 instrument** → "루프 시연 용이성" 최우선.
2. FR-1 "flow 1회" 유지 위해 **instance 단위** label (설계당 1 스칼라는 데이터 1점뿐).
3. instance 단위 후보 3종(A path slack / B net routability / C net wirelength) 중 **A** — STA `*.rpt` 파싱이 가장 저렴, 단일 스칼라 회귀, tabular CPU 학습과 정합. B는 congestion map·CNN/GNN·GPU로 NFR-1(신규 의존성·고정 예산) 충돌.

설계:
- **feature (합성 직후)**: path별 logic depth·fanout·driven cell 종류·추정 net 수·시작/끝 유형. *합성 후 STA*에서.
- **label (최종)**: 동일 path의 *post-route STA* slack(ns). 샘플 1개 = 1 timing path → flow 1회로 수천 샘플.
- **val 지표**: path slack 예측 MAE(ns) ↓ (단일 스칼라, selection 정합).
- **추출 (NFR-2 frozen / NFR-3 오픈소스)**: OpenROAD/Yosys + OpenSTA `report_checks`를 **합성 후·라우팅 후 두 시점** 모두 떠야 함 (숨은 비용 — `prepare.py` 고정 추출 스펙의 핵심).

종속 제약 전파:
- **002**: feature를 path 단위 합성 feature로 한정. critical-path 쏠림 대응(informative sampling).
- **003**: per-path라 1 설계로 수천 샘플. train/val 분할은 path가 아니라 **설계/클럭그룹 단위 grouping**으로 누수 차단.
- **004**: 스칼라 회귀 → **tabular(XGBoost/MLP)**로 강하게 기울어짐, GNN 불요 (NFR-1 충돌 해소).
- **005**: 사람-수작업 baseline 후보 — 합성 단계 slack을 그대로 쓰는 naive predictor / 선형회귀. 정량 임계값은 데이터 확정 후 **spec**에서 nail down (INTENT-vs-spec invariant).
