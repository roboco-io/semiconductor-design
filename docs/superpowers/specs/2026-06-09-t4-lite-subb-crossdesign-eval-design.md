# T4-lite Sub-B — held-out 설계 교차검증 평가 기계 설계

- **status**: approved (Operator brainstorming 승인 2026-06-09, 결정 브리프 추천 묶음)
- **결정 출처**: [decision brief](../decisions/2026-06-09-t4-lite-subb-crossdesign-eval.md) (D1~D6).
- **프로그램**: T4-lite의 **Sub-B**(평가 기계). Sub-A(다설계 데이터 획득, AWS $)는 별도 후속.
- **scope**: `src/pipeline/validation.py` 추가 — Operator 소유. `train.py`·`prepare.py`·`dataset` frozen 무변경.

## 1. 동기

현 검증 게이트(`run_validation_gate`)는 *within-design* 랜덤 K-fold일 뿐, **미관측 설계 일반화**를
측정하지 못한다(`fold_splits`가 group 무시). Codex 리뷰가 외적 타당성 병목으로 지목. Sub-B는
**held-out 설계 평가 기계 + 리포트**를 만든다(결론은 Sub-A 실데이터 후). 인프라는 준비됨:
`train.py`는 group≥2면 design-disjoint split, `prepare.py --design-id`는 group_key 스탬프.

## 2. 결정 (브리프 확정)

| # | 결정 | 값 |
|---|---|---|
| D1 | CV 방식 | **Leave-One-Design-Out (LODO)** — 설계당 1 fold |
| D2 | verdict 근거 | **방향성 probe** — K/D 설계 우세 + 평균 격차, 통계 유의성 주장 안 함 |
| D3 | 통합 형태 | **신규 함수** `run_crossdesign_gate` (기존 게이트 불변) |
| D4 | promote 편입 | **보류** — 리포트 전용(Sub-A 데이터 후 별도 결정) |
| D5 | 테스트 | **합성 다설계 fixture**(group_key 3개) |
| D6 | 범위 | 기계 + 리포트 + 테스트 (데이터·편입은 밖) |

## 3. 아키텍처 (단위별 책임, 모두 `validation.py` 추가)

### 3.1 `design_fold_splits(groups) -> list[tuple[list[int], list[int]]]`
- LODO: `groups`(=각 행의 group_key 리스트)에서 unique 설계마다 1 fold.
  fold = (val=그 설계 행 인덱스, train=나머지 전부).
- unique 설계 < 2면 `ValueError`("교차설계엔 ≥2 설계 필요") — 단일 설계(현 데이터)에선 호출 불가가 정상.
- 설계 순서는 **정렬-안정**(sorted unique)으로 결정적.

### 3.2 `run_crossdesign_gate(winner_train_py, baseline_train_py, rows, workdir, *, naive=True) -> dict`
- `groups = [r["group_key"] for r in rows]`; `splits = design_fold_splits(groups)`.
- 기존 `candidate_fold_maes(winner, rows, splits, workdir/"winner")` ·
  `candidate_fold_maes(baseline, rows, splits, workdir/"baseline")` · `naive_fold_maes(rows, splits)` 재사용.
  → 설계별(=fold별) held-out MAE 3계열.
- **방향성 집계**(D2): fold별 `diff = winner_mae - baseline_mae`. inf(실패 fold) 있으면 그 설계는 "검증불가"로 표시하고 집계에서 제외(전부 inf면 verdict `unverifiable`).
  - `n_designs`, `n_winner_better`(diff<0 수), `mean_gap`(유한 diff 평균), 설계별 `(design, winner_mae, baseline_mae, naive_mae)`.
  - `verdict`: `"generalizes_better"` if `n_winner_better > n_valid/2`, `"mixed"` if 동수, `"worse"` if 과반 열세, `"unverifiable"` if 유효 fold 0.
- 반환 dict: 위 필드 + `single_design=False`(교차설계임 표시) + `per_design` 리스트.
- **통계 유의성(Wilcoxon/CI) 미산출**(D2) — 소수 설계 과신 차단.

### 3.3 `render_crossdesign_report(res) -> str`
- 설계별 표(design · naive · baseline · winner held-out MAE) + `n_winner_better/n_designs` + `mean_gap` + verdict.
- **저표본 caveat 명시**: "설계 N개 → 통계 검정 불가, 이건 일반화 *probe*(경향)이지 유의성 주장 아님.
  설계 더 확보(Sub-A) 시 강한 결론 가능." + "train.py 내부 분할 포함 nested resampling(within-design과 동일 한계)."

## 4. 데이터 흐름

```
다설계 dataset(rows, group_key 2+)
  → design_fold_splits(groups) → 설계당 1 fold (val=그 설계, train=나머지)
  → candidate_fold_maes(winner/baseline) + naive_fold_maes  (fold=설계별 held-out MAE)
  → 방향성 집계: n_winner_better/n_designs, mean_gap, per_design 표, verdict
  → render_crossdesign_report (저표본·nested resampling caveat 포함)
```

## 5. 에러 처리

- 설계 < 2 → `design_fold_splits`가 `ValueError`(호출자가 "교차설계 불가, 단일 설계" 처리).
- 후보가 어떤 설계 fold에서 실패(inf) → 그 설계 "검증불가" 표기, 유효 fold만 집계. 전부 inf → `unverifiable`.
- `candidate_fold_maes`의 nested-resampling·inf 처리(기존)를 그대로 계승.

## 6. 테스트 (TDD, 합성 fixture)

- `design_fold_splits`: 3개 group_key(A/B/C) → 3 fold, 각 fold val=한 설계·train=나머지, 인덱스 분리·전체 합·결정적 순서. 단일 group → `ValueError`.
- `run_crossdesign_gate`(real train.py, 작은 3-설계 합성 jsonl): winner==baseline → mean_gap≈0·verdict `mixed`; broken winner → `unverifiable`.
- `render_crossdesign_report`: 설계별 행·`n/N`·mean_gap·저표본 caveat 문구·"probe" 포함.
- 기존 73 tests green 유지(기존 게이트·fold_splits 무변경).

## 7. INTENT 정합

- `train.py`·`prepare.py`·`dataset` frozen 무변경(validation 읽기·임시분할만). 신규 함수만 추가.
- "측정 엄밀·과장 금지" 정합: 소수 설계에서 통계 유의성 주장 대신 방향성 probe + 저표본 caveat.
- Learnings #1("합성으로 결론 내지 말 것")을 *결론이 아닌 기계 테스트*로 준수 — 일반화 결론은 Sub-A 후.
- 자동 promote 기준 무변경(D4) — 교차설계 게이트는 현재 리포트 전용.

## 8. 범위 밖 (후속)

- **Sub-A**: 실제 다설계 데이터 획득(Fargate aes/sha3, AWS $).
- 교차설계 게이트를 auto-promote AND에 편입(Sub-A 후).
- 설계 충분 시 통계 검정 주지표화(방향성 → 유의성 승격).
- 설계별 샘플 불균형 가중·정규화.
