# Spec — T1 승격 게이트를 교차설계(repeated LODO) 통계 게이트로 재정의 (2026-06-20)

## 1. 문제 (맥락)
gen-006에서 강화된 program.md로 winner가 **처음 LODO 통과**(`generalizes_better`, 우세 2/3)했으나,
T1(`run_validation_gate`, 혼합 repeated K-fold = *in-distribution* 정확도)에서 `worse`로 차단됨
(`rejected_t1`). 게이트 체인이 `median → LODO → T1 → Codex`인데:

- **LODO**(`run_crossdesign_gate`): 설계 단위 held-out → 교차설계 일반화 (프로젝트 north star).
- **T1**(`run_validation_gate`): 설계 *혼합* K-fold → in-distribution 정확도 (피벗 이전 단일설계 잔재).

둘이 부분 상반된 목표를 측정 → **stated bar(=LODO) ≠ enforced bar(=LODO AND in-distribution T1)**.
결정 brief `docs/superpowers/decisions/2026-06-20-lodo-t1-gate-conflict.md` 의 "Operator 결정
(2026-06-20)" 절에서 선택지 **A**(T1을 교차설계로 재정의) + 세부 **A2**(repeated LODO 통계판)를
기록. 본 spec은 그 A2 결정의 구현 명세다.

## 2. 결정
다설계 dataset에서 T1 게이트의 fold 스킴을 **혼합 repeated K-fold → repeated leave-one-design-out**
으로 교체한다. T1이 LODO와 *같은 축*(교차설계 일반화)을 측정하되, LODO(방향성 probe)보다 엄밀한
**통계 검정**(paired Wilcoxon + bootstrap CI)을 제공한다. 단일설계 dataset에서는 기존 혼합 K-fold T1을
유지(교차설계 평가 불가).

## 3. 설계

### 3.1 fold 증식 — `repeated_design_fold_splits(groups, repeats, base_seed)`
- leave-one-design-out × `repeats` seed → `D × repeats` fold. 각 fold = `(train_idx, val_idx, seed)`:
  - `val_idx` = held-out 설계 d의 인덱스, `train_idx` = 나머지 설계.
  - `seed = base_seed + r` (r = 0..repeats-1) — train.py 내부 0.75 분할을 변동시켜 같은 (train,val)
    설계 쌍에서도 다른 모델/MAE를 산출(반복의 원천).
- `D ≥ 2` 필요(단일설계 ValueError). 설계 순서는 sorted-unique로 결정적.

### 3.2 fold별 seed 주입 — split 소비자 *모두* 3-tuple 허용
3.1의 split이 3-원소 `(tr, va, seed)`가 되므로, **splits를 분해하는 모든 함수**가 2-tuple과 3-tuple을
함께 받아야 한다(아니면 깨짐). 영향받는 소비자는 둘:
- `candidate_fold_maes` — `run_candidate(..., seed=0)` 고정을 → split의 seed(있으면) 사용하도록 확장.
  반복의 원천(train.py 내부 0.75 분할이 seed로 변동). seed 미존재(2-tuple) → seed=0.
- `naive_fold_maes` — naive는 학습이 없어 seed와 무관하지만, 현재 `for _tr, va in splits`로 2-tuple만
  분해한다. **3-tuple도 받도록** 인덱싱(`va = split[1]`)으로 일반화 — seed는 무시. paired fold 순서는
  candidate와 동일 splits를 쓰므로 보존된다.
- **하위 호환**: 기존 2-원소 `(tr, va)` split은 두 함수 모두 seed=0/seed-무시로 동작(혼합 K-fold T1·
  기존 호출자 불변). 회귀 테스트로 보장(§7).

### 3.3 교차설계 T1 게이트 — `run_crossdesign_validation_gate(winner, baseline, rows, workdir, repeats, base_seed, alpha)`
- `repeated_design_fold_splits`로 fold 생성 → winner/baseline/naive를 동일 fold에서 paired 평가.
- winner 또는 baseline이 **한 fold라도 inf** → `verdict="worse"`(검증 불가, 보수적). 기존 T1과 동일.
- `paired_comparison(winner_folds, baseline_folds)` → `verdict()` 재사용:
  - `distinguishable`: p<alpha **AND** CI 전체 < 0 (winner가 유의하게 낮음=좋음) → 승격 후보.
  - `worse`: p<alpha AND CI 전체 > 0. 그 외 `indistinguishable`.
- 반환 dict는 기존 T1과 동일 키 + `"scheme": "repeated_design_lodo"`, `"repeats"`, `"n_designs"`.

### 3.4 orchestrator 분기
- 다설계(≥2 group_key) → LODO 게이트 통과 후 **`run_crossdesign_validation_gate`** 호출.
- 단일설계 → 기존 `run_validation_gate`(혼합 K-fold) 유지.
- 게이트 주입(`gate_fn`)은 테스트 mock 위해 유지. 기본값만 분기.

### 3.5 리포트
- `render_validation_report`에 `scheme` 분기: 교차설계면 제목/캡션을 "교차설계 T1(repeated LODO)"로,
  단일설계 한계 경고(§) 대신 **상관 caveat**(같은 held-out 설계 반복은 상관 → CI 낙관적) 표기.

## 4. 임계값 (spec 권한 — INTENT/plan은 인용만)
- `alpha = 0.05` (기존 T1과 동일).
- `repeats = 10` (D=3 → 30 fold). 기존 혼합 T1의 50 fold보다 작으나 상관 구조라 독립 파워는 더 낮음 —
  **보수적 해석 전제**. repeats는 향후 설계 확보(Sub-A) 시 재조정 가능한 파라미터.
- 승격 조건 불변: `verdict_vs_baseline == "distinguishable"` AND Codex `approve`.

## 5. 통계 한계 (정직한 서술)
- 같은 held-out 설계의 `repeats` 반복은 강하게 상관(동일 val set) → paired Wilcoxon/CI는 독립 가정보다
  **낙관적**(불확실성 과소평가). 리포트에 명기, verdict 보수적 해석.
- D=3은 교차설계 표본이 근본적으로 작음 — 강한 일반화 결론은 **설계 확보(Sub-A) 후**. 본 spec은 게이트가
  *옳은 축*을 측정하게 만드는 것이 목적이지, D=3에서 강한 유의성을 주장하지 않는다.
- nested resampling(train.py 내부 0.75 분할 포함) 한계는 기존과 동일.

## 6. Not (범위 밖)
- train.py/prepare.py/dataset frozen 계약 무변경 (읽기 + 임시 fold 분할만).
- LODO 방향성 게이트(`run_crossdesign_gate`) 무변경 — 방향성 probe로 유지(빠른 차단 + naive 포함 리포트).
- 임계값을 INTENT/plan에서 재정의 금지(여기 §4가 single source).
- 설계 확보(Sub-A, AWS) 본 spec 범위 밖 — 별도.

## 7. 성공 기준 (사전 고정)
- 다설계 dataset에서 T1이 교차설계 fold로 동작(혼합 K-fold 미사용)함을 테스트가 검증.
- **split 소비자 2-tuple/3-tuple 호환 회귀 가드**: `candidate_fold_maes`가 3-tuple split의 seed를
  `run_candidate`에 전달(2-tuple → seed=0)하고, `naive_fold_maes`가 3-tuple split에서 seed를 무시한 채
  `va = split[1]`로 동작하며 paired fold 순서를 보존함을 테스트가 검증.
- winner 부분실패(inf) fold → `worse` 차단 회귀 가드.
- 단일설계 dataset → 기존 혼합 T1 경로 유지(회귀 가드).
- gen-006 winner를 이 게이트로 재평가 시 verdict가 in-distribution과 *다를 수 있음*(교차설계축 측정 확인).
- 전체 테스트 green + ruff.
