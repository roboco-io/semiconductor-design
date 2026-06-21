# `train.py` 레퍼런스 — surrogate 학습 단일 파일

> **이 문서의 범위**: 현재 `train.py` 코드가 *실제로 무엇을 어떻게* 하는지(데이터 흐름·함수·하이퍼파라미터)와
> 에이전트가 변형하는 법. *왜 이렇게 설계했나*(결정 근거)는 [설계 spec](superpowers/specs/2026-06-06-od4-train-baseline-design.md),
> *무엇을 바꾸면 안 되나*(불변 규칙)는 [[frozen-contract]](../wiki/frozen-contract.md) 참고 — 이 문서는 그 둘과 겹치지 않게 *구현*에 집중한다.

## 1. 한눈에

`train.py`는 AutoResearch 루프에서 **에이전트(Claude/Codex)가 유일하게 변형하는 파일**이다.
`prepare.py`가 만든 frozen `dataset.jsonl`을 읽어 per-endpoint timing slack 회귀 모델을 학습하고,
검증 MAE 한 줄(`{"val_mae": <float>}`)을 stdout에 출력하며 `model.joblib`을 저장한다. 이 `val_mae`가
세대 selection의 단일 지표다.

```
$ uv run python train.py --data dataset.jsonl --out /tmp/run --seed 0
{"val_mae": 0.1042}        # ← stdout 마지막 줄(계약). runner가 이 한 줄을 파싱.
# /tmp/run/model.joblib    # ← 저장된 파이프라인(나중에 held-out 재채점에 쓰임)
```

**현재 버전은 gen-001 winner**(Codex가 만든 `VotingRegressor` + 13개 파생 feature)가 승격된 챔피언이다.
에이전트가 새 후보를 만들 때 이 파일을 baseline으로 받아 변형한다.

## 2. 입출력 계약 (불변 — 어기면 후보 무효)

| 항목 | 값 |
|---|---|
| CLI | `--data <dataset.jsonl>` `--out <dir>` `--seed <int>` (시그니처 불변) |
| stdout | 마지막 줄에 `{"val_mae": <float>}` JSON 한 줄 (낮을수록 좋음) |
| 산출물 | `<out>/model.joblib` (joblib 직렬화된 sklearn Pipeline) |
| import | `sklearn`·`numpy`·`joblib`·`click`·stdlib만 (신규 의존성 금지) |
| 입력 스키마 | 8 feature + `post_route_slack_ns`(라벨) + `group_key` (아래 §4) |

전체 계약은 [[frozen-contract]](../wiki/frozen-contract.md)·[program.md](../program.md). harness는 에이전트가
소스 대신 산문을 반환하면 `_looks_like_source`(ast.parse + 토큰 검사)로 걸러 baseline fallback한다.

## 3. 데이터 흐름

```
main(--data, --out, --seed)
  └─ load_rows(data)          # jsonl → list[dict]  (§5.1)
  └─ build_xy(rows)           # → X(8열), y, groups  (§5.2)
  └─ train_and_eval(X,y,groups,seed)
       ├─ split(...)          # train/val 인덱스     (§5.4) ← 교차설계 측정의 핵심
       ├─ make_model(seed)    # Pipeline 생성        (§5.5)
       │    └─ add_timing_features  (§5.3, 13개 파생 feature)
       ├─ model.fit(X[tr], y[tr])
       └─ mean_absolute_error(y[va], model.predict(X[va])) → val_mae
  └─ joblib.dump(model) + echo {"val_mae": ...}
```

## 4. 입력 스키마 (frozen — `prepare.py` 출력과 일치)

`FEATURE_NAMES`(8개, 순서 불변), 라벨 `LABEL = post_route_slack_ns`, 그룹 `GROUP = group_key`.

| # | feature | 의미 |
|---|---|---|
| 0 | `num_stages` | 경로의 논리 단계 수 |
| 1 | `synth_slack_ns` | 합성 직후 timing slack(ns) — 예측의 출발점 |
| 2 | `synth_arrival_ns` | 합성 직후 신호 도착 시각(ns) |
| 3 | `max_stage_delay_ns` | 단계별 지연의 최댓값 |
| 4 | `mean_stage_delay_ns` | 단계별 지연의 평균 |
| 5 | `startpoint_is_ff` | 시작점이 플립플롭인가(0/1) |
| 6 | `endpoint_is_ff` | 끝점이 플립플롭인가(0/1) |
| 7 | `path_group` | 경로 그룹(문자열 → ordinal 인코딩, §5.2) |

라벨 `post_route_slack_ns`는 **배선 후** 최종 slack — surrogate가 합성 직후 feature로 *미리 맞히려는* 값이다.
`group_key`는 설계 식별자(gcd·aes·ibex·jpeg). feature가 아니라 **교차설계 분할용**(§5.4)으로만 쓴다.

## 5. 함수별 상세

### 5.1 `load_rows(data_path) -> list[dict]`
`dataset.jsonl`을 줄 단위로 파싱. 빈 줄은 건너뛰고, JSON 오류 시 `파일:줄번호`를 붙여 재발생(디버깅 친화).

### 5.2 `build_xy(rows) -> (X, y, groups)`
- `path_group`(문자열)을 **정렬-안정 ordinal**로 인코딩: `sorted({path_group})` 순서로 0,1,2…를 부여.
- 8열 float 행렬 `X`, 라벨 벡터 `y`, 설계 리스트 `groups`를 반환.
- ⚠️ **주의(코드 주석)**: `pg_code`는 *전체 rows*로 만든다. inference 시 일부 subset만으로 `build_xy`를
  다시 부르면 path_group 코드가 어긋난다 — held-out 재채점은 같은 인코딩을 유지해야 한다.

### 5.3 `add_timing_features(X) -> X_ext` — **현재 챔피언의 핵심**
원본 8 feature에 **도메인 파생 13개**를 덧붙여 21열로 확장(에이전트가 "문제를 미리 씹어준" 부분).

| 파생 feature | 식 | 직관 |
|---|---|---|
| `total_mean_delay` | `stages * mean_delay` | 경로 전체 평균 지연 총합 |
| `delay_spread` | `max_delay - mean_delay` | 지연 편차(불균형) |
| `delay_ratio` | `max_delay / (|mean_delay|+eps)` | 최대/평균 지연 비 |
| `slack_per_stage` | `synth_slack / (stages+eps)` | 단계당 slack 여유 |
| `arrival_per_stage` | `arrival / (stages+eps)` | 단계당 도착 부담 |
| `criticality` | `arrival - synth_slack` | 경로의 빠듯함 |
| `ff_pair` | `start_ff * end_ff` | 양끝 모두 FF인가 |
| `boundary_ff_count` | `start_ff + end_ff` | 경계 FF 개수(0/1/2) |
| (곱) | `synth_slack*mean_delay`, `arrival*mean_delay`, `stages*max_delay` | 비선형 상호작용 |
| `pg_sin`/`pg_cos` | `sin(path_group)`, `cos(path_group)` | ordinal 그룹의 순환 인코딩 |

`eps=1e-9`로 0 나눗셈을 막는다. 이 함수는 `FunctionTransformer`로 Pipeline에 들어가 **모델과 함께 pickle**된다(§7 함정).

### 5.4 `split(X, y, groups, seed) -> (tr, va)` — **교차설계 측정의 결정점**
- **설계 ≥2개**(다설계 dataset): `GroupShuffleSplit(test_size=0.25)` → val이 **train에 없는 설계**로
  구성된다. 따라서 `val_mae`는 *학습에서 안 본 설계*에 대한 예측 성능 = **교차설계 일반화의 대리 지표**.
- **단일 설계**: `train_test_split`(고정 seed random 25%).
- 이 한 분기가 selection 지표의 의미를 정한다. 승격 게이트의 LODO·교차설계 T1은 이 위에서 한 번 더 검증한다([[gate-chain]](../wiki/gate-chain.md)).

### 5.5 `make_model(seed) -> Pipeline` — 현재 챔피언 모델
2-stage Pipeline: `features`(add_timing_features) → `model`(VotingRegressor).

| 추정기 | 주요 하이퍼파라미터 | 가중치 |
|---|---|---|
| `HistGradientBoostingRegressor` | lr=0.055, max_iter=420, max_leaf_nodes=31, l2=0.02, min_samples_leaf=12 | 0.58 |
| `ExtraTreesRegressor` | n_estimators=360, max_features=0.85, min_samples_leaf=2, bootstrap=False | 0.42 |

두 모델의 가중 평균(0.58:0.42). HGB는 "실수에서 점진적으로 배우는" 부스팅, ExtraTrees는 "여러 갈래로
빠르게 추정하는" 랜덤 트리 — 성격이 다른 둘을 섞어 한쪽 실수를 메운다. `seed`는 두 모델과 split에 전파된다.

### 5.6 `train_and_eval` / `main`
`split` → `make_model` → `fit(train)` → `predict(val)` → `mean_absolute_error` → `(model, val_mae)`.
`main`은 click CLI로 이를 묶고 `model.joblib` 저장 + `val_mae` 출력.

## 6. 에이전트 변형 가이드 (이 파일만 바꾼다)

**자유롭게 바꿔도 되는 것** — 이 안에서 새 아이디어를 시도:
- 모델 교체/튜닝: sklearn 내 회귀기(`HistGradientBoosting`/`RandomForest`/`ExtraTrees`/`GradientBoosting`/`MLPRegressor` 등), 하이퍼파라미터, 앙상블 구성·가중치.
- feature 엔지니어링: `add_timing_features`의 파생 항목 추가/교체, 정규화(per-design 표준화·무차원 비율·델타 라벨 등 — probe 실측은 [program.md](../program.md) "관찰 힌트" 참고).
- split 전략: 단 `val_mae`가 교차설계 일반화를 측정하도록 GroupShuffleSplit 계열 유지를 권장.

**바꾸면 후보 무효(계약)**:
- CLI 시그니처(`--data/--out/--seed`), stdout `{"val_mae"}` 형식, `model.joblib` 저장, 8 `FEATURE_NAMES`.
- 신규 의존성 추가, 다중 파일 분할, GPU·딥러닝 프레임워크.

> 변형 결과는 median(5-seed) → LODO → 교차설계 T1 → Codex 게이트를 통과해야 승격된다.
> "in-loop `val_mae`를 낮추는 것"과 "미관측 설계 일반화"는 다를 수 있다(gen-004~008 실증) — 게이트는 후자를 본다.

## 7. 함정 / 주의

- **`FunctionTransformer` pickle**: `add_timing_features`는 모델과 함께 `model.joblib`에 직렬화된다.
  모듈 최상위 함수여야 pickle이 풀린다(gen-001에서 `__main__` 참조로 held-out 재채점이 깨진 마찰 → `holdout.py` 보강). 커스텀 함수를 추가할 때 동일 주의.
- **path_group 인코딩 일관성**(§5.2): 학습·재채점이 같은 ordinal 매핑을 써야 한다. subset으로 `build_xy` 재호출 금지.
- **단일 파일 self-contained**: `FEATURE_NAMES`를 `prepare.py`와 따로 재선언한다 — dataset 스키마가 바뀌면 양쪽을 맞춰야 한다(현재 frozen).
- **sklearn 추정기 규약**: 커스텀 추정기를 `VotingRegressor`에 넣으려면 sklearn 규약(`get_params`/`fit`/`predict`)을 지켜야 한다(gen-004 cand-001이 위반해 fit 크래시 → inf 도태).

## 8. 관련 문서
- 설계 결정: [`docs/superpowers/specs/2026-06-06-od4-train-baseline-design.md`](superpowers/specs/2026-06-06-od4-train-baseline-design.md)
- 불변 계약: [`wiki/frozen-contract.md`](../wiki/frozen-contract.md)
- 게이트 체인: [`wiki/gate-chain.md`](../wiki/gate-chain.md) · 데이터 준비: [`prepare.py`](../prepare.py)
- 에이전트 지시문: [`program.md`](../program.md) · 세대 이야기: [`experiments/`](../experiments/README.md)
