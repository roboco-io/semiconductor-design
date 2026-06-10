# Feature 정규화 probe — 교차설계 전이 실패 대응 설계

- **status**: approved (Operator brainstorming 승인 2026-06-11)
- **동기 출처**: [crossdesign.md](../../../experiments/multidesign/crossdesign.md) — gcd+aes LODO 2-fold에서
  winner·baseline 모두 naive(항등 예측)에 ~20× 격차로 패배(분포 shift 지배).
- **결정 lineage**: [ibex vs 조기 게이트 브리프](../decisions/2026-06-10-suba-ibex-vs-early-gate.md) →
  옵션 A 실측 → "ibex 지출 전 feature 정규화 재평가 선행" 결론의 실행.
- **scope**: Operator 일회성 probe 실험(루프 과제화 아님 — 그건 결과 본 후 별도 결정).
  frozen(prepare.py·train.py·dataset) 전부 무변경.

## 1. 목적 · 산출물

분포 shift로 무력화된 교차설계 전이를 **"어느 정규화 축이 전이를 살리는가"** 로 분해 실측한다.

- 산출물: `experiments/multidesign/probe/` 변형 3개 + 드라이버 + `probe.md` 리포트
  (변형×설계 MAE 표 + 사전 고정 판정) + INTENT Learnings 기록.
- 최종 payoff: **ibex run-task 진행/보류 결정 근거** + (transferable 변형 발견 시) program.md 힌트 후보.

## 2. 클래리파잉 결정 (Operator 확정)

| # | 질문 | 결정 |
|---|---|---|
| Q1 | 누가 정규화를 찾는가 | **Operator probe**(일회성 실험). 루프 과제화는 결과 후 별도 결정 |
| Q2 | 성공 기준 | **naive 기준 사전 고정**(아래 §5) — post-hoc 기준 이동 금지(gen-002 교훈) |
| Q3 | 변형 묶음 | **B: 축별 분해**(V1·V2·V3 각각 + 대조군). 조합(V1×V3)은 두 축 모두 생존 시 후속 |

## 3. 구성요소 (전부 Operator-owned, frozen 무변경)

`experiments/multidesign/probe/` 아래, 각 변형은 **현 winner train.py의 전체 사본**에서
정규화 부분만 수정(통제 변인: 정규화만 다름). train.py 계약(`--data/--out/--seed`,
stdout `{"val_mae"}`, `model.joblib`) 유지 — 기존 채점기를 그대로 재사용하기 위함.

- **`v1_delta.py` — 델타 label(잔차 학습)**: label을 `post_route_slack_ns − synth_slack_ns`로
  학습·예측. 설계 간 label 오프셋(gcd 음수 vs aes 양수)을 label에서 제거.
  **MAE 동일성**: |Δ̂−Δ| = |(synth+Δ̂)−(synth+Δ)| 이므로 델타 공간 MAE = 절대 slack MAE —
  다른 변형·대조군과 그대로 비교 가능. naive(델타=0)와 출발점이 같아 §5 기준과 정확히 정렬.
- **`v2_groupstat.py` — 설계별 통계 상대화**: `build_xy`에서 수치 feature를 *그 행의 설계*
  (group_key)별 synth 통계(평균·표준편차)로 표준화. **label은 무변경**(MAE 스케일 보존).
  held-out 설계는 자기 synth 통계를 사용 — synth는 추론 시점에 이미 있는 정보라 누수 아님.
  std=0 가드: `_DENOM_EPS = 1e-9` 패턴 재사용(상수 feature → 0으로).
- **`v3_ratio.py` — 무차원 비율 feature**: 절대 ns feature 4개를 무차원 비율 3개로 교체 —
  `mean_stage_delay/max_stage_delay`, `synth_slack/synth_arrival`, `max_stage_delay/synth_arrival`.
  유지: `num_stages`(무차원), `startpoint_is_ff`, `endpoint_is_ff`, `path_group` 코드 → 총 7 feature.
  0-분모 가드는 `_DENOM_EPS` 패턴 동일.
- **`run_probe.py` — 드라이버**: multidesign 744행 → `design_fold_splits`(LODO 2-fold) →
  {v1, v2, v3, winner(train.py), baseline(`619e24f~1`)} 각각 `candidate_fold_maes`
  + `naive_fold_maes` → §5 판정 → `probe.md` 생성. fold 작업물은
  `tempfile.TemporaryDirectory`(126M 교훈).

**채점 메커니즘 (기존 재사용, 무수정)**: `score_holdout`은 변형 모듈 자신의 `build_xy`로
held-out feature·y를 만들고 변형의 `model.joblib`로 예측한다 — feature 표현 변경이 변형
스크립트 안에 캡슐화되고 harness는 그대로. `__main__` pickle 등록도 기존 처리 재사용.

## 4. 데이터 흐름

```
experiments/multidesign/dataset.jsonl (744행, frozen — 기존 산출물 재사용)
  → design_fold_splits → [(train=gcd, val=aes), (train=aes, val=gcd)]
  → 변형/대조군별 candidate_fold_maes (tempdir) + naive_fold_maes
  → 판정(§5) → experiments/multidesign/probe/probe.md
```

## 5. 판정 규칙 (사전 고정 — 결과 확인 전 변경 금지)

naive 기준점(2026-06-10 실측): aes 1.7198 / gcd 1.4117.

| verdict | 조건 |
|---|---|
| `transferable` | 변형 MAE가 **두 held-out 설계 모두** naive 미만 |
| `partial` | 한 설계만 naive 미만 |
| `not_transferable` | 두 설계 모두 naive 이상 |
| `unverifiable` | 어느 fold라도 inf(학습/채점 실패) — 침묵 스킵 금지, 리포트 명기(D5 정신) |

**후속 행동 매핑**: ≥1개 변형 `transferable` → ibex 확장 가치 있음(3-fold로 강화) +
program.md 힌트 후보. 전부 `not_transferable` → "이 feature 표현 한계" 결론 — ibex 보류,
대안(피처 소스 확장·분포 겹치는 설계 선택)을 새 브리프로. 2-fold 저표본 caveat은 항상 병기.

## 6. 에러 처리 · 재현성

- 변형 실패는 해당 변형 inf → `unverifiable`로 격리, 드라이버는 계속(다른 변형 결과 보존).
- seed=0 고정, 행 순서는 결합 dataset 그대로, fold는 sorted-unique 설계 순 — 전 과정 결정적.
- 작업물 tempdir 자동 정리. `probe.md`·변형 스크립트만 git에 남김.

## 7. 테스트

- 변형 3개 각각: 합성 fixture(2설계 소형 jsonl)로 train.py 계약 준수 스모크
  (exit 0, stdout val_mae 파싱, model.joblib 존재, score_holdout 왕복).
- 판정 함수(naive 비교 → verdict) 단위 테스트: 4 verdict 경로 + 경계(동률은 naive 이상으로).
- 기존 83 tests green 유지. probe는 일회성 — 과한 테스트는 비범위(YAGNI).

## 8. INTENT 정합

- **frozen 무변경**: prepare.py·train.py·gcd/aes/multidesign dataset 전부 불변 —
  gen-001~003 비교성 무손상. 변형은 `experiments/` 하위 사본(루프 후보 아님).
- **맹목적 자율 금지**: probe는 Operator 실험이며 승격·머지와 무관. 루프 편입(program.md
  힌트, cross-design 지표)은 결과 확인 후 *별도 spec*.
- **사전 고정 판정**(§5): gen-002 위양성 교훈 — 결과 보고 기준을 옮기지 않는다.
- **비용**: 전 과정 로컬 CPU, AWS·LLM 호출 0([[project-subscription-only-no-metered-llm]] 무관).

## 9. 범위 밖 (후속 결정)

- V1×V3 조합 변형(두 축 생존 시), 루프 과제화(cross-design 지표를 selection/게이트에 편입).
- ibex run-task(probe 결과에 따라 새 결정 브리프), 4+ 설계 통계 검정.
- prepare.py에 정규화 feature 영구 편입(데이터 계약 변경 — 별도 spec + 비교성 논의 필수).
