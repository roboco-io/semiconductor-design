# T1 — 승격 검증 게이트 (Promotion Validation Gate)

- **status**: approved (Operator brainstorming 승인 2026-06-07)
- **프로그램**: "Trustworthy Automated Research for EDA Surrogates" 의 **1단계(T1)**.
  순차 로드맵 **T1 → T3 → T4 → T2** (각자 별도 spec→plan→구현):
  - **T1 (이 문서)**: 엄밀 평가 토대 — 승격 직전 통계적 검증 게이트 + gen-001 소급 재심.
  - **T3**: reasoning trace / provenance 평면 (각 변형의 "왜" 구조화 캡처).
  - **T4**: held-out *설계* 교차 일반화 (다설계 확보 후 — T1의 "진짜 held-out" 형태).
  - **T2**: 자기개선 평가 루프 (에이전트가 평가 프로토콜 개선 제안 + 메타-게이트). capstone.
- **lineage**: gen-002 단일 seed 위양성 → median harness
  ([2026-06-06-multiseed-median-selection-design](2026-06-06-multiseed-median-selection-design.md))
  의 후속. median이 "싼 선택"을 고쳤다면, T1은 "주장의 신뢰성"을 고친다.

## 1. 동기

gen-001은 winner val_mae 0.177→~0.11(seed=0)로 H-A("에이전트가 baseline 능가")를 확증했다고
기록됐다. 그러나 gen-002에서 단일 seed 선택이 위양성임이 드러났고, 5-seed median 재판정에서
gen-001 winner(현 baseline)의 median은 0.0865였다. **점추정 하나로는 "정말 이겼나"를 알 수 없다.**

핵심 사실(2026-06-07 grounding): 실데이터 `dataset.jsonl`은 **53행·전부 gcd·core_clock·
startpoint_is_ff=1** — `group_key`·`path_group`이 단일값. **현 설계 안에는 구조적으로 hold-out할
그룹이 없다.** 따라서 T1은 *단일 설계 내 repeated K-fold*로만 엄밀화 가능하며, 진짜 held-out
*설계* 일반화는 T4(다설계)의 몫이다. 이 한계를 게이트가 **명시 출력**한다.

## 2. 설계 결정 (Operator 확정)

| # | 결정 | 값 | 근거 |
|---|---|---|---|
| D1 | 게이트 위치 | **승격 직전 검증 게이트** (선택 지표 대체 아님) | 싼 5-seed median 루프 유지, 승격 시에만 엄밀 비용 |
| D2 | 결정 권한 | **advisory** — 자동 거부 없음, Operator가 결정 | H-B 보존, 게이트는 통계적 근거만 주입 |
| D3 | resampling | **repeated 5-fold CV ×10** (총 50 fold) | 분산↔시간 균형, 53행 노이즈 완화 |
| D4 | 비교 집합 | **naive · baseline · winner** 3-way, **동일 fold(paired)** | 공정 비교, H-A는 winner<baseline 검정 |
| D5 | 통계 | paired **Wilcoxon signed-rank** + 평균차 **bootstrap 95% CI** + 효과크기 | 소표본·비정규 robust |
| D6 | 정직성 | "단일 설계 n=53 — 일반화 주장 불가, held-out 설계는 T4 필요" 명시 출력 | 과장 방지, T4 동기화 |

## 3. 아키텍처 (단위별 책임)

### 3.1 `src/pipeline/validation.py` (신규, 순수 분석 — Operator 소유)
- `repeated_kfold_mae(train_py, dataset, k=5, repeats=10, base_seed=0) -> list[float]`
  - 각 (repeat, fold)에서 train_py를 학습·평가해 fold별 MAE 리스트(길이 50)를 반환.
  - **paired 보장**: 동일 (repeat, fold) split을 baseline·winner·naive에 *모두* 적용
    (split 인덱스를 한 번 생성해 세 모델에 공유).
- `naive_mae_folds(dataset, splits) -> list[float]`
  - naive 예측 = "합성 슬랙(`synth_slack_ns`)을 최종 슬랙으로 그대로 사용". 각 fold val에서 MAE.
- `paired_comparison(a_folds, b_folds) -> {mean_diff, ci_low, ci_high, wilcoxon_p, effect_size}`
  - `a-b` fold별 차이의 bootstrap(10k resample, 고정 시드) 평균차 95% CI + Wilcoxon signed-rank p
    + 효과크기 = **Cohen's dz**(차이 평균 / 차이 표준편차, paired 표준 효과크기). 차이 표준편차 0이면
    dz=0으로 처리하고 경고.
- `verdict(comp, alpha=0.05) -> "distinguishable" | "indistinguishable" | "worse"`
  - winner가 baseline보다 유의하게 낮고(p<alpha) CI가 0을 넘지 않으면 `distinguishable`,
    CI가 0을 포함하면 `indistinguishable`, 유의하게 높으면 `worse`.

### 3.2 `train.py` 호출 계약 — **무변경**
- 기존 `run_candidate`/subprocess 경로를 재사용하되, **fold split을 외부에서 주입**해야 paired가
  성립한다. train.py는 `--seed`만 받으므로, validation은 **train.py를 직접 import하지 않고**
  데이터셋을 fold로 물리 분할한 임시 jsonl을 만들어 `--data`로 넘기는 방식
  (train.py의 내부 split 대신 *validation이 split을 통제*). train.py·prepare.py·dataset 불변.
  - 주의: train.py 내부가 자체 train/val split을 하므로, validation은 **train fold만 train.py에
    넘기고**, val fold의 예측·MAE는 validation이 별도 계산해야 paired가 정확하다. → train.py의
    학습 산출물(model.joblib)을 로드해 val fold를 예측(holdout.py 패턴 재사용).
  - 이 "model.joblib 로드 후 외부 val 채점" 경로는 기존 `holdout.py`가 이미 가진 능력
    (gen-001 winner의 `__main__` pickle 이슈 포함) — 재사용·확장.

### 3.3 `validation_report.md` 생성기
- 3-way 표(naive/baseline/winner: mean MAE ± std, fold 분포), winner-vs-baseline·winner-vs-naive
  paired 결과(CI·p·효과크기), 한 줄 verdict, **단일설계 경고 블록**.

### 3.4 `operator_gate` 연동
- `operator_gate.promote()` 흐름에 **검증 리포트 생성·표시 단계 추가**(승격 *전*). 리포트는
  winner_val_mae 점추정 옆에 CI·p·verdict를 나란히 둔다. promote 자체는 여전히 Operator 수동.

## 4. 데이터 흐름

```
dataset.jsonl (53행)
  → validation: 50개 (repeat,fold) split 인덱스 생성 (고정 base_seed)
  → 각 split: baseline·winner는 train fold로 train.py 학습 → model.joblib → val fold 예측 → MAE
              naive는 val fold에서 |synth_slack - post_route_slack| 평균
  → fold별 MAE 3 계열 (각 길이 50, paired)
  → paired_comparison(winner, baseline), paired_comparison(winner, naive)
  → verdict + validation_report.md (단일설계 경고 포함)
  → operator_gate가 승격 전 표시
```

## 5. 에러 처리

- train.py가 어떤 fold에서 실패(non-zero/timeout) → 그 fold MAE `inf`; 게이트는
  **"검증 불가(후보 불안정)"** 로 verdict를 `worse`에 준하게 처리하고 실패 fold 수를 리포트.
- bootstrap/Wilcoxon은 fold MAE에 inf가 있으면 거부하고 사유 출력(엄밀성 보호).
- fold 수가 통계에 부족하면(예: 유효 fold < 10) verdict `indistinguishable` + 경고.

## 6. gen-001 소급 재심

- 구현 후 이 게이트를 **gen-001 winner(현 train.py) vs (가상의 pre-gen-001 baseline) vs naive**에
  적용. pre-gen-001 baseline 소스는 `experiments/gen-001/` 또는 git 이력에서 확보.
- 산출: `experiments/gen-001/revalidation.md` — H-A 첫 확증이 엄밀 잣대로도 유지되는지의 verdict.
  (예상: 단일 설계라 `indistinguishable` 가능성 — 그 자체가 T4 필요성의 근거.)
- **Operator 게이트**: 재심 결과로 gen-001 status를 바꾸는 건 Operator 승인 후에만.

## 7. 테스트 (TDD)

- `repeated_kfold_mae`: split 개수=50, paired split 동일성(같은 인덱스가 세 모델에 공유).
- `naive_mae_folds`: 합성-슬랙 naive 계산 정확성(수기 계산과 일치).
- `paired_comparison`: 알려진 입력에서 CI·Wilcoxon p·효과크기 수치 검증(고정 시드 bootstrap).
- `verdict`: 세 경계(유의 낮음/CI 0 포함/유의 높음) 분기.
- inf fold 처리: 실패 fold가 verdict·리포트에 반영.
- 단일설계 경고 문자열이 리포트에 항상 포함.
- frozen 무변경: validation은 train.py/prepare.py/dataset를 수정하지 않음(읽기/임시분할만).

## 8. INTENT 정합

- train.py·prepare.py·dataset **무변경**(읽기·임시 fold 분할만). 새 분석 모듈만 추가(Operator 소유).
- 게이트 **advisory** → H-B(사람 승격) 보존, 오히려 통계적 근거로 강화.
- verdict 임계(alpha=0.05 등)는 **이 spec이 처음 정의** — INTENT/plan은 복사 인용만(재정의 금지).
- "절대 PPA가 아니라 거버넌스/프로세스 novelty" 정합: 본 게이트는 *주장의 신뢰성*과 *승격 거버넌스*를
  강화하는 것이지 PPA 절대치를 좇지 않는다. 단일설계 한계 명시가 over-claim을 차단.

## 9. 범위 밖 (다음 단계로)

- held-out *설계* 교차 일반화 → **T4**.
- 변형의 "왜" 캡처 → **T3**.
- 에이전트가 평가 프로토콜 자체를 개선 → **T2**.
- 자동 승격/거부 — 본 게이트는 advisory only.
