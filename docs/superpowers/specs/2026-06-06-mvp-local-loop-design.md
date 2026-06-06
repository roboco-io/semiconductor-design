# MVP Local AutoResearch Loop 설계 (sub-project A)

> status: approved (2026-06-06, brainstorming) · 후속: writing-plans
> 영향: [`issues/005`](../../../issues/005-comparison-baseline-thresholds.md) (OD-5 ground)
> 불변: INTENT Not(자율 무인 머지 금지·Operator authority) · train.py 단일 파일 변형 · prepare.py·dataset 스키마 frozen.
> 분해: 본 spec은 **A(로컬 루프)**. **B(cloud batch/HUGI, FR-3 병렬)**는 별도 spec 연기.

## 1. 범위

로컬 단일 머신에서 AutoResearch 진화 **1세대**를 끝까지 수행: candidate-gen → 로컬 실행 → selection → **Operator 승인** → git tag. 데이터 = Fargate 검증 53-샘플(`experiments/real-gcd-fargate`, flow_lockfile_sha `bff0e2e5`). 전부 CPU.

## 2. 컴포넌트 (`src/pipeline/`, 작은 순수 단위)

| 단위 | 책임 | 의존 |
|---|---|---|
| `candidate_gen.py` | baseline `train.py` + `program.md`(baseline 지시) + 전략 프롬프트 → **Claude Code SDK & Codex SDK headless** 호출 → 변형 train.py N개(전략×SDK). 각 후보 = reversible patch. baseline 불변, `experiments/gen-NNN/candidates/<id>/train.py`에 기록. | SDK(주입 가능 — mock TDD) |
| `runner.py` | 각 후보 `python <cand>/train.py --data <dataset.jsonl> --out <cand>/art` subprocess → stdout `{"val_mae"}` 파싱. 순차(CPU sklearn은 ms). 실패 후보는 val_mae=inf로 기록. | stdlib |
| `selection.py` | 후보 중 최저 val_mae winner + 전체 순위. 순수 함수. | — |
| `operator_gate.py` | winner+diff+순위 요약 제시 → **Operator 승인 입력 대기**. 승인 시만 git tag `gen-NNN-best` + winner를 root `train.py`로 승격. 거절 시 baseline 불변. | git |
| `orchestrator.py` | 위를 엮는 1세대 CLI (`semi-loop` / `make loop`). | 위 4개 |

## 3. 상태/ERD 매핑 (`experiments/gen-NNN/`)

- `generation.json` = **GENERATION**(gen_no, baseline_ref, status, winner_candidate_id).
- `results.tsv` = **CANDIDATE**(id, strategy, sdk, patch_ref, val_mae, is_winner) + **JOB**(val_metric, train_time) 흡수.
- winner `model.joblib` = CANDIDATE.artifact. **DATASET** = 53-샘플(flow_lockfile_sha).
- serverless-autoresearch `results.tsv` 스타일 계승.

## 4. 루프 (1세대 흐름)

1. Operator가 `program.md`(baseline 지시)·`config.yaml`(N, 전략) 설정.
2. `candidate_gen` → N후보(Claude n/2 + Codex n/2, 전략 conservative/moderate/aggressive 다양).
3. `runner` → 후보별 val_mae.
4. `selection` → winner + 순위.
5. **`operator_gate`** → Operator 검토·승인 → git tag + baseline 승격, 또는 거절.

## 5. OD-5 (실데이터 ground)

53-샘플 측정: **naive(합성 slack=label) MAE 1.41 ns** vs 현 HistGBDT **0.177 ns**(8× 우월 — H-A 축소판 지지).
- baseline = naive(1.41 reference). **H-A 지지 = winner val MAE < naive**. selection은 val_mae 최소화.
- 정밀 임계값·통계 유의는 **다설계 데이터 후 spec**(단설계 random split 낙관 주의 — INTENT-vs-spec invariant: 임계값은 spec이 nail down).

## 6. val-gaming 방어 (설계 §6, 최소 포함)

orchestrator가 **held-out test** 분할 보유(후보 train.py 미관측). winner `model.joblib`을 test로 재채점 → val↔test 격차로 과적합/게이밍 탐지. Operator 거절 경로(INTENT 엣지케이스 "val 지표만 좋은 경우").

## 7. Operator authority (H-B 핵심)

baseline `train.py`는 승인 전까지 **불변**(후보는 별도 디렉터리). winner 승격·git tag는 **사람만**. 자율 무인 머지 없음. 구조가 H-B를 강제.

## 8. 테스트 (fixture-first)

SDK 호출을 **주입 가능 인터페이스 + mock**(결정론적 가짜 변형 train.py 반환)으로 오케스트레이터 로직(gen→run→select→gate) TDD. runner는 합성 dataset + 실제 train.py subprocess로 검증. 실제 SDK 호출(비용)은 통합 smoke — **Operator 확인 후**.

## 9. 비목표 (YAGNI)

- cloud batch/HUGI 병렬(B, 별도 spec).
- 다설계·License Gate.
- 다세대 자동 연속(세대마다 Operator 정지 — H-B).
- reasoning trace 증거 평면(2차).
