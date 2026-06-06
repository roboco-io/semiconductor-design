# OD-4 + train.py Baseline 설계

> status: approved (2026-06-06, brainstorming) · 후속: train.py writing-plans
> 근거: [`docs/knowledge-base/2026-06-06-od4-model-class-research.md`](../../knowledge-base/2026-06-06-od4-model-class-research.md) (grounded)
> 영향: [`issues/004`](../../../issues/004-model-class-tabular-vs-gnn.md) (OD-4 resolved)
> 불변: OD-1 = per-endpoint timing slack 회귀(val=MAE). prepare.py·dataset.jsonl 스키마 frozen (NFR-2).

## 1. 결정 (OD-4)

- **모델 클래스 = scikit-learn tabular**, baseline = `HistGradientBoostingRegressor` (LightGBM급 GBDT).
- **NFR-1 허용 의존성 = scikit-learn (+numpy)**. 에이전트는 이 안에서만 — 신규 의존성 금지.
- 근거: MasterRTL이 path-level timing에 RandomForest/XGBoost를 쓰고 GCN/Transformer 압도; 일반 tabular ML도 GBDT가 heavy-tailed(critical-path 쏠림)·소중 데이터서 NN 우월. CircuitNet의 CNN/GNN은 우리가 피한 spatial 태스크용. (반례 TabPFN은 <3000서 우월하나 PyTorch 의존 → NFR-1 차단.)
- sklearn-only를 XGBoost 대신 택한 이유: 한 import로 HistGBDT/RandomForest/ExtraTrees/GBR/MLP를 줘 **에이전트 모델-교체 변형 공간**이 넓고(H1b), SOTA 실질 동급, 의존성 최소.

## 2. eval 경계 (Operator 결정: train.py가 전체 소유, karpathy 스타일)

train.py가 split·학습·val MAE 계산을 *전부* 소유하고 에이전트가 변형. 원본 AutoResearch 충실. val 게이밍 위험은 **루프 레벨 held-out test 재채점 + Operator 검토**로 방어(§6).

## 3. train.py 계약 (fixed — karpathy 최소)

에이전트는 train.py 전체를 변형하되, 루프가 소비하는 최소 계약만 고정:
- **입력**: `--data <dataset.jsonl>` — prepare.py frozen 스키마(8 feature + `post_route_slack_ns` + `group_key`).
- **출력**: stdout에 `{"val_mae": <float>}` 한 줄 (JSON). 루프 selection이 *최소화*.
- **artifact**: `--out <dir>/model.joblib` 저장 (ERD `CANDIDATE.artifact_uri`; §6 재채점 hook).
- 고정 CPU 학습 예산 내 완료.

## 4. baseline 내용 (에이전트 출발점, 계약 외 전부 가변)

- rows 로드 → `X`(8 feature, `path_group` 인코딩) / `y = post_route_slack_ns`.
- split: group ≥2면 **group-disjoint**(by `group_key`=design_id), 단설계(group 1)면 fixed-seed random split.
- `HistGradientBoostingRegressor` 기본값 fit → val 예측 → `mean_absolute_error` → `{"val_mae": mae}` 출력 + `model.joblib` 저장.

## 5. 에이전트 변형 공간 (H1b idea diversity)

모델 패밀리 교체(HistGBDT↔RandomForest↔ExtraTrees↔GBR↔MLPRegressor) · 하이퍼파라미터 · feature 엔지니어링/선택/인코딩 · split 전략. **신규 의존성 0**(sklearn+numpy만).

## 6. val-gaming 방어 (루프 scope, 연기)

train.py가 val을 소유하므로 에이전트가 val에 과적합/게이밍 가능. 방어:
- 루프가 **held-out test**(train.py 미관측)를 보유, winner의 `model.joblib`을 test로 재채점 → 일반화 진짜 수치 + 게이밍 탐지.
- Operator 검토(INTENT 엣지케이스 "val 지표만 좋은 경우 → 거절").
- 본 설계 범위 밖 — 진화 루프(FR-2~4) 구현 시.

## 7. fixture-first 구축

train.py를 prepare.py처럼 fixture-first TDD. 2-sample 실 fixture는 학습 부족 → train.py 테스트용 **합성 `dataset.jsonl`(수십 행, group 2개)** fixture 생성. 테스트는 *계약*(실행·`{"val_mae"}` valid JSON·`model.joblib` 저장·MAE 산출·group split) 검증, 모델 품질 아님. 실제 학습 품질은 실데이터(issues/006) 단계.

## 8. 비목표 (YAGNI)

- 진화 루프(candidate gen/batch/select) — 별도(FR-2~4).
- XGBoost·GNN·TabPFN — §1 근거로 제외.
- held-out test 루프 구현 — §6 연기.
