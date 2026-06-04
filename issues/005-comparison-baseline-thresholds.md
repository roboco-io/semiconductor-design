---
id: 005
title: 비교 baseline·정량 임계값
status: open
type: decision
blocks: ["PRD §9 가설 지지 조건"]
related_prd: OD-5
related_intent: "Why §확인방법 (임계값은 데이터셋 확정 후), 품질 기준"
depends_on: [001, 003]
---

# 005 — 비교 baseline · 정량 임계값

## 배경

가설 H-A는 "surrogate winner val 지표 < 사람-수작업 baseline"이다 (PRD §9). 그러나 (1) *사람-수작업 baseline*을 무엇으로 둘지, (2) "더 낮다"의 정량 임계값(절대 차이? 통계 유의?)이 미정. INTENT `Why §확인방법`은 이를 "데이터셋 확정 후"로 명시 연기했다.

> **권한 주의 (INTENT-vs-spec invariant)**: 정량 임계값은 본 issue나 PRD가 *재정의하지 않는다*. 데이터셋 확정 후 **설계 spec에서 nail down**하고, PRD §9·INTENT는 인용만 한다.

## 옵션

### baseline (무엇과 비교하나)
- **A. 단순 baseline 모델** — feature 평균/선형회귀 등 naive predictor.
- **B. 공개 논문 보고 수치** — CircuitNet 등 동일 태스크 보고 지표 (데이터 다르면 직접 비교 불가).
- **C. Operator 1회 수작업 튜닝** — 사람이 1회 손으로 튜닝한 모델.

### 임계값 (얼마나 나아야 지지)
- 절대 차이 vs 상대 % vs 통계적 유의(반복 seed).

## 결정 기준

- 001 지표 단위·003 데이터 규모 확정이 선행 (분산 추정 가능해야 유의성 판단).
- baseline이 *재현 가능*해야 함 (같은 데이터셋·`flow_lockfile_sha`).
- H-B(Operator-in-loop 성능 손실 없음) 비교도 동일 baseline 프레임 사용.

## 액션 아이템

- [ ] 001·003 확정 후 baseline 종류 선택.
- [ ] 정량 임계값을 **설계 spec**에 기록 (PRD/issue 아님).
- [ ] seed 반복 횟수·유의성 기준 정의.
