# Decision Brief — T4-lite Sub-B: held-out 설계 교차검증 평가 기계

> 목적: 이 문서는 **선택을 위한 정보**다. 각 결정마다 선택지의 summary·상세·pros·cons·내 추천을
> 정리한다. 읽고 결정해 주면 그대로 spec으로 옮긴다. (추천은 참고용 — 다른 선택도 동등하게 유효.)

## 배경 (grounding, grep 확인됨)

- `train.py`는 group(=design) ≥2면 **이미 design-disjoint split**(train.py:119, GroupShuffleSplit).
- `prepare.py --design-id`는 설계별 dataset에 `group_key` 스탬프(다설계 = 설계별 실행 후 결합).
- `docker/eda-flow`는 `DESIGN` env 파라미터화 → aes/sha3는 env만 변경.
- **유일한 코드 공백**: `validation.py`의 `fold_splits`가 plain `KFold`(group 무시) → 현재 T1 게이트는
  *within-design* 랜덤 K-fold일 뿐. **held-out *설계* CV가 없다** = Sub-B가 채울 부분.
- Sub-B는 **평가 기계 + 리포트**까지. 실제 다설계 데이터(Sub-A, AWS $)·일반화 *결론*은 Sub-A 이후.

---

## 결정 D1 — 교차검증 방식

**무엇을 정하나**: 미관측 설계에 대한 일반화를 어떤 CV로 측정할지.

### 옵션 1-A. Leave-One-Design-Out (LODO) — 추천
- **Summary**: 설계 D개면 D fold. 각 fold = (나머지 D−1 설계로 학습 → 그 1개 설계 전체로 예측·채점).
- **상세**: "한 번도 못 본 설계를 예측하나?"를 가장 직접적으로 묻는다. fold 간 train/test 설계가 완전 분리 → fold가 *진짜 독립*.
- **Pros**: 질문과 1:1 대응(미관측 설계 예측력). 데이터 최대 활용(매번 D−1 설계로 학습). 구현 단순.
- **Cons**: 설계가 2~3개면 fold도 2~3개뿐 → 통계 검정력 거의 없음(D2 참조). 설계별 샘플 수 불균형이 결과를 흔들 수 있음.

### 옵션 1-B. Repeated Grouped K-fold (GroupKFold × repeats)
- **Summary**: 설계를 그룹으로 묶어 k개 그룹-분리 fold를 만들고 여러 번 반복.
- **상세**: 설계 수가 많을 때(예: 5+) fold 수를 조절. 2~3개면 사실상 LODO와 동일(k=D).
- **Pros**: 설계가 많아지면 자연 확장. 반복으로 추정 안정.
- **Cons**: 소수 설계(2~3)에선 LODO와 차이 없음 + 복잡도만 추가. "그룹 묶기"가 설계 수 적을 때 임의적.

### 옵션 1-C. 설계 쌍 hold-out (pairwise)
- **Summary**: 설계 쌍마다 한쪽으로 학습→다른쪽 예측(방향 양쪽).
- **Pros**: D개로 D(D−1)개 방향 관측 → fold 수 늘림.
- **Cons**: train 설계가 1개뿐이라 학습 빈약(현실성 낮음). 해석 복잡.

**추천: 1-A (LODO)** — 설계가 소수인 lite 단계에 질문과 정확히 맞고 가장 단순. 설계가 늘면(full T4) 1-B로 자연 승격. **함의**: fold 수가 적다는 약점은 D2(verdict)에서 정직하게 흡수.

---

## 결정 D2 — 교차설계 verdict의 근거 (정직성 핵심)

**무엇을 정하나**: 설계 2~3개(=fold 2~3개)에서 "winner가 baseline보다 일반화 잘한다"를 무엇으로 말할지.
**왜 중요**: fold가 적으면 통계(Wilcoxon/CI)는 검정력이 사실상 0(n=2~3). 과장하면 위양성, 과소하면 무의미.

### 옵션 2-A. 방향성 probe — 추천
- **Summary**: 미관측 설계 K/D개에서 winner MAE < baseline MAE + 설계별 격차 표 + 평균 격차. "유의성" 주장 안 함.
- **상세**: 리포트가 "일반화 *경향*"으로 프레이밍하고 "n_designs 작아 통계 검정 불가 — 이건 probe"를 명시.
- **Pros**: 소수 설계에 정직. 위양성 위험 최소. 프로젝트의 "측정 엄밀·과장 금지" 가치와 정합.
- **Cons**: "유의하다"는 강한 주장은 못 함(설계 더 모으기 전까지). 자동 승격 기준으로 쓰기엔 약함.

### 옵션 2-B. 통계(Wilcoxon+CI) + 강한 caveat
- **Summary**: 기존 paired 기계 그대로 적용하되 "n_designs 작아 검정력 낮음" 경고를 크게.
- **Pros**: 기존 `paired_comparison` 재사용(구현 최소). 설계 늘면 그대로 유효.
- **Cons**: n=2~3에서 p값·CI가 *수치로* 출력돼 오독 위험(특히 자동 게이트가 그 p를 읽으면). Codex가 원래 경고한 "과신"을 재발시킬 소지.

### 옵션 2-C. 둘 다 (방향성 주 + 통계 부)
- **Summary**: K/D+격차를 주지표로, p/CI를 참고로 함께 보고.
- **Pros**: 정보 최대. 설계 늘면 통계가 주지표로 자연 승격.
- **Cons**: 리포트·구현 복잡. 두 지표가 엇갈릴 때(방향성 좋은데 p 큼) 해석 혼란.

**추천: 2-A (방향성 probe)** — lite 단계 설계 수에 정직하고, 자동 게이트가 약한 p값을 신뢰하는 사고를 원천 차단. 설계가 충분해지면(full T4) 2-C/통계로 승격. **함의**: 교차설계 게이트는 당장 *자동 승격 기준*이 아니라 *generalization 리포트*다(D4 참조).

---

## 결정 D3 — 기존 게이트와의 통합 형태

**무엇을 정하나**: held-out 설계 평가를 코드에 어떻게 끼울지.

### 옵션 3-A. 신규 함수 `run_crossdesign_gate(...)` — 추천
- **Summary**: within-design `run_validation_gate`는 그대로 두고, 교차설계용 별도 함수 추가(`design_fold_splits` + per-design MAE + 방향성 집계).
- **Pros**: 두 평가(within-design 통계 게이트 vs cross-design probe)가 *개념적으로 다른 것*임을 코드가 드러냄. 각자 단순·독립 테스트. 기존 게이트·테스트 무변경.
- **Cons**: 일부 로직(candidate_fold_maes·naive_fold_maes 재사용) 중복 호출. 함수 2개.

### 옵션 3-B. `run_validation_gate(..., mode="design")` 파라미터
- **Summary**: 한 함수에 mode 분기(random K-fold vs design LODO).
- **Pros**: 단일 진입점. 호출부 일관.
- **Cons**: 한 함수가 두 책임(통계 게이트 + 방향성 probe) — verdict 의미·리포트가 mode마다 달라 분기 복잡. "한 파일/함수=한 책임" 원칙과 마찰.

**추천: 3-A (신규 함수)** — within-design 통계 게이트와 cross-design probe는 *목적·verdict·검정력*이 달라 분리가 맞다. `design_fold_splits`(LODO)·`run_crossdesign_gate`·`render_crossdesign_report` 추가, 기존 함수 불변.

---

## 결정 D4 — 자동 승격 게이트(AND)에 지금 편입할까

**무엇을 정하나**: 교차설계 결과를 gen 루프의 promote 기준(현 median+T1+Codex)에 *지금* 넣을지.

### 옵션 4-A. 리포트 전용(편입 보류) — 추천
- **Summary**: Sub-B는 평가 기계 + 리포트까지만. promote 기준은 *안 바꿈*. 실제 다설계 데이터(Sub-A) 확보 후 별도 결정.
- **Pros**: 데이터 없이 기준 바꾸면 의미 없음(현재 단일 설계라 LODO 불가). 범위 명확·작게. 방향성 probe(약한 verdict)를 성급히 자동 차단/승격에 쓰지 않음.
- **Cons**: 루프가 아직 교차설계로 자동 판정하진 않음(그건 Sub-A 후 후속).

### 옵션 4-B. 지금 AND에 편입
- **Summary**: promote = median ∧ T1 ∧ Codex ∧ cross-design 방향성.
- **Pros**: 자율 게이트가 일반화까지 강제.
- **Cons**: **지금은 불가능**(단일 설계 → LODO fold 0). 데이터 전엔 死코드. 약한 probe를 hard gate로 쓰면 위양성/위음성.

**추천: 4-A (리포트 전용)** — 현재 데이터로 LODO 자체가 불가하므로 편입은 Sub-A 후가 자연. Sub-B는 *기계가 준비됨*을 합성 fixture로 증명하는 데 집중.

---

## 결정 D5 — 테스트 데이터(합성 vs 실데이터 파생)

**무엇을 정하나**: Sub-B를 무엇으로 검증할지.

### 옵션 5-A. 합성 다설계 fixture — 추천
- **Summary**: group_key A/B/C 3개 가짜 설계로 된 작은 jsonl을 테스트에서 생성. LODO split·per-design MAE·집계·리포트 문구를 검증.
- **Pros**: 비용 0, 결정적, 빠름. 기계의 *정확성*(split 분리·집계 산식)을 또렷이 검증.
- **Cons**: *일반화 결론*은 검증 못 함(그건 Sub-A 실데이터 몫) — 단, Sub-B 목표가 결론이 아니라 기계라 무방.

### 옵션 5-B. 기존 gcd 53행을 인위 분할해 "유사 다설계"
- **Summary**: gcd 행을 num_stages 등으로 쪼개 가짜 group_key 부여.
- **Pros**: "실데이터 비슷한" 분포.
- **Cons**: 진짜 설계 차이가 아니라 인위적 — 오해 소지. 합성 fixture 대비 이점 적음.

**추천: 5-A (합성 fixture)** — Sub-B는 *기계의 정확성* 검증이 목적. 일반화 결론은 명시적으로 Sub-A로 미룸(프로젝트 Learnings #1 "합성으로 결론 내지 말 것"을 *결론이 아닌 기계 테스트*로 준수).

---

## 결정 D6 — Sub-B 범위 경계 (확인용)

**제안 범위**: `design_fold_splits`(LODO) + `run_crossdesign_gate`(per-design winner/baseline/naive MAE +
방향성 집계) + `render_crossdesign_report`(설계별 표 + K/D + 평균격차 + 저표본 caveat) + 합성 fixture 테스트.
**범위 밖**: 실제 다설계 데이터 획득(Sub-A) · promote 기준 편입(D4-A) · 통계 검정 주지표화(설계 충분해진 뒤).

---

## 요약 — 추천 묶음

| 결정 | 추천 | 한 줄 이유 |
|---|---|---|
| D1 CV | LODO | 미관측 설계 예측을 직접 측정, 소수 설계에 단순 |
| D2 verdict | 방향성 probe | fold 2~3개에 통계는 과신 위험 — 경향+격차로 정직 |
| D3 통합 | 신규 함수 | within-design 통계 게이트와 별개 책임 |
| D4 promote 편입 | 보류(리포트 전용) | 데이터 없이 편입 무의미, Sub-A 후 |
| D5 테스트 | 합성 fixture | 기계 정확성 검증, 결론은 Sub-A로 |
| D6 범위 | 기계+리포트+테스트 | 데이터·편입은 범위 밖 |

이 묶음대로 가도 좋고, 개별 결정을 바꿔도 된다. 결정해 주면 spec으로 옮긴다.
