---
id: 003
title: 데이터 규모 (flow 1회로 라벨 수 충분한가)
status: open
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
