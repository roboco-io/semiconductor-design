# Issues

로컬 이슈 트래커 (피벗 후 재생성, 2026-06-04). GitHub push 이후 `gh issue create`로 이전 가능.

> 피벗 이전 이슈(001~007, L1/L2/L3·Gate 좌표계)는 `archive/integrated-program-3layer` 브랜치에 보존.
> 현재 좌표계는 [`PRD.md`](../PRD.md) Open Decisions(OD-N) + FR/NFR + [`INTENT.md`](../INTENT.md).

| ID | 제목 | 상태 | PRD 출처 | blocks |
|---|---|---|---|---|
| [001](001-surrogate-metric-definition.md) | surrogate 지표 정의 → **per-path timing slack 회귀** | ✅ resolved (2026-06-04) | OD-1 | FR-1·FR-3·§9 임계값 |
| [002](002-feature-set-composition.md) | feature_set 구성 (합성 리포트 어느 필드까지) | ✅ resolved (2026-06-04) | OD-2 | FR-1 |
| [003](003-dataset-scale-label-count.md) | 데이터 규모 → **endpoint 단위 다설계** (F3 재설계) | ✅ resolved (revised 2026-06-06) | OD-3 | FR-1 |
| [004](004-model-class-tabular-vs-gnn.md) | 모델 클래스 (tabular vs GNN, CPU 학습 가능성) | open | OD-4 | NFR-1·train.py |
| [005](005-comparison-baseline-thresholds.md) | 비교 baseline·정량 임계값 | open | OD-5 | §9 가설 지지 조건 |
| [006](006-eda-flow-execution-infra.md) | EDA flow 실행 인프라 (ECS Fargate 유력) | open | §8 plane / F4 | FR-1 실 데이터셋 |

## 의존 순서

`001` (지표 정의)이 다른 4개의 선행 — 지표가 정해져야 feature(002)·라벨 규모(003)·모델(004)·임계값(005)이 확정 가능. 데이터셋 1회 생성(FR-1)이 002·003을 경험적으로 닫는다.

**001 resolved (per-path timing slack)** → 002~005에 OD-1 제약이 전파됨: 002는 path feature로, 003은 누수 차단 grouping으로, 004는 tabular로, 005는 naive(feature slack=label) baseline으로 좁혀졌다. 다음 선행은 데이터셋 생성(FR-1, `prepare.py`)이 002·003을 경험적으로 닫는 것.

## 이슈 작성 규칙

프론트매터: `id, title, status (open/resolved), type (decision), blocks, related_prd, related_intent`.
본문 구조: 배경 / 옵션 / 결정 기준 / 액션 아이템. 해결 시 `status: resolved` + 본문 맨 아래 `## Resolution`.

> **권한 주의**: 정량 임계값(005)은 데이터셋 확정 후 **설계 spec에서 nail down**한다. 본 issues나 PRD는 임계값을 *재정의하지 않는다* (INTENT-vs-spec invariant).
