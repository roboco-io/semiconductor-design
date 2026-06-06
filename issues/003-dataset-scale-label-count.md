---
id: 003
title: 데이터 규모 (flow 1회로 라벨 수 충분한가)
status: resolved
type: decision
blocks: [FR-1]
related_prd: OD-3
related_intent: "What §핵심기능 1 (flow 1회 → feature+label 쌍)"
depends_on: [001]
---

# 003 — 데이터 규모 / 라벨 수

> **OD-1 확정 (001 resolved, 2026-06-04)**: per-path slack → **1 설계로 수천 path 샘플** 확보 가능, "flow 1회"(FR-1) 유지. 남은 핵심 과제는 **train/val 분할 누수 차단** (path가 아니라 설계/클럭그룹 단위 grouping).

## 배경

FR-1은 "EDA flow **1회** 실행으로 데이터셋 자가생성"을 전제한다. 001 확정으로 per-path 단위라 1 설계 1회 실행으로 수천 path 샘플이 나온다 — 규모 문제는 대부분 해소. 남은 위험은 같은 설계의 path가 train/val 양쪽에 들어가는 **누수**다.

## 옵션

- **A. 단일 설계, 내부 분할** — 1개 오픈 설계의 net/cell 단위 라벨 → 수천~수만 샘플 가능 (routability/net 단위).
- **B. 복수 설계 sweep** — 여러 오픈 설계 × 파라미터. "flow 1회" 정의를 "1 batch"로 완화 필요 (NFR/FR 재확인).
- **C. 합성 단계 다중 스냅샷** — 동일 설계의 중간 단계별 feature/label.

## 결정 기준

- 001 지표의 라벨 granularity (설계 단위 vs net 단위).
- "flow 1회" 제약(FR-1)을 유지하면서 충분한 N 확보 가능한가.
- 학습/검증 분할 시 누수 없는 grouping (같은 설계가 train/val 양쪽에 들어가지 않도록).

## 액션 아이템

- [ ] 001 지표의 라벨 단위 확정 후 1회 실행 예상 샘플 수 추정.
- [ ] 부족하면 "flow 1회" 정의 완화 여부를 PRD FR-1과 함께 재검토.
- [ ] train/val 분할 grouping 규칙 정의 (`prepare.py` freeze 전).

## Resolution (2026-06-04, prepare.py 구현)

per-path라 1 설계 1회 실행으로 수천 path 샘플. 누수 차단: `group_key = f"{design_id}:{path_group}"` 컬럼을 부여, train/val 분할은 **group-disjoint**(같은 design:clock 그룹이 양쪽에 들어가지 않음). join 키 = (startpoint, endpoint, path_group), 미매칭 path는 drop. 실제 라벨 수 충분성은 real-flow 실행 시 경험적으로 재확인(현재 fixture-first).

## F3 재설계 (2026-06-06, 실제 gcd 검증이 위 가정 falsify)

⚠️ 실제 gcd 검증에서 두-시점 critical path가 **disjoint** → 위 per-path join이 0 rows. per-path 단위 폐기, **endpoint 단위 다설계**로 재설계:
- 샘플 = **(design_id, endpoint)**, join 키 = (design_id, endpoint) + `path_type=max`. endpoint는 stage 간 안정 → join 보장.
- 규모 = **Σ(설계별 #endpoint)** — 단설계 path 대신 **다설계 batch**(gcd→ibex→aes…). "flow 1회" → 다설계 batch 완화.
- grouping = **design_id 단위** group-disjoint (`group_key=design_id`).
- 다설계 실행은 [`006`](006-eda-flow-execution-infra.md) Fargate 병렬이 값싸게 함.

출처: `docs/superpowers/specs/2026-06-06-f3-endpoint-pairing-design.md`. 파서 재키 수정은 별도 writing-plans.
