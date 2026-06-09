# Decision Brief — Sub-A 진행점: ibex 추가 vs 2-fold 조기 게이트

> 목적: gcd+aes(2설계) 확보 상태에서 다음 한 걸음을 고르기 위한 정보. 각 옵션의 내용·비용·얻는 것·
> pros·cons·추천. 읽고 결정하면 그대로 실행. (실제 ibex run-task는 비용 게이트 — 동의 후에만.)

## 현재 상태 (사실)

| 설계 | 샘플 | label(post_route_slack_ns) 범위 | 성격 |
|---|---|---|---|
| gcd | 53 | **−1.37 ~ 0** (음수, 빡빡) | 작은 산술 코어, 타이밍 tight |
| aes | 691 | **+0.44 ~ +2.93** (양수, 여유) | 암호 블록, 타이밍 loose |

- 교차설계 게이트(`run_crossdesign_gate`, Sub-B)는 **구현·테스트 완료**. 지금 gcd+aes에 돌리면 LODO **2 fold**:
  (train=gcd → predict aes) · (train=aes → predict gcd). 무비용(로컬 CPU).
- 게이트는 **gen-001 winner(현 train.py) vs pre-gen-001 baseline(사람)** 을 각 held-out 설계에서 비교 →
  "에이전트 winner가 사람 baseline보다 *미관측 설계에* 더 잘 일반화하나?"(= H-A의 일반화 버전).

## ⚠️ 중요 — 분포 shift가 결과를 지배할 수 있다

gcd(음수 slack)와 aes(양수 slack)는 **분포가 정반대**다. gcd로 학습한 모델이 aes를 예측하면 *winner든
baseline이든* 크게 빗나갈 수 있다(한 번도 본 적 없는 양수 영역). 가능한 결과 시나리오:

1. **둘 다 크게 틀림, 구분 미미** → verdict `mixed`. → 정직한 발견: "surrogate는 2개 분포-shift 설계
   간 자동 전이가 안 된다(더 많은/다양한 설계 필요)". *negative지만 의미 있는 결과*.
2. **winner가 baseline보다 덜 틀림** → verdict `generalizes_better`. → H-A가 일반화로도 약하게 지지.
3. **winner가 더 틀림** → verdict `worse`. → 에이전트의 gcd-특화 feature가 aes에 역효과(과적합 신호).

어느 쪽이든 **2 fold는 통계적으로 매우 약함**(설계 1개가 verdict를 뒤집음). 방향성 probe로만 해석.

## 옵션 A — 2-fold 게이트 먼저 (무비용) · 추천

- **내용**: 지금 gcd+aes로 `run_crossdesign_gate` 실행 → `experiments/multidesign/`(2설계) + crossdesign.md 리포트.
- **얻는 것**: ① 기계가 *실데이터*에서 작동하는지 확인(합성 fixture만 거쳤음) ② 분포-shift 일반화의 *첫 실신호* ③ ibex 지출 전 의사결정 근거.
- **Pros**: 비용 0, 즉시. "비싼 단계(ibex) 전 싼 검증" 패턴. 실데이터로 게이트 검증.
- **Cons**: 2 fold = 가장 약한 probe. 분포 shift가 결과를 지배해 `mixed`로 뭉개질 수 있음(단 그것도 발견).
- **비용**: 없음.

## 옵션 B — ibex run-task 먼저 (AWS 비용)

- **내용**: ibex Fargate run-task → 수집 → prepare → 그 다음 3-fold 게이트.
- **얻는 것**: 3 설계(gcd·aes·ibex) → LODO 3 fold. ibex는 큰 RISC-V 코어 → 샘플 多·분포 또 다름 → probe 강화.
- **Pros**: 처음부터 3-fold(더 의미 있는 방향성). 설계 다양성↑(소형 gcd·암호 aes·CPU ibex).
- **Cons**: **AWS 실 과금**. ibex는 aes(74분)보다 크므로 **runtime 길고(수 시간 가능)·마찰 위험↑**(CTS·route
  시간↑, 큰 설계일수록 flow 실패 가능성↑). 조기 신호 없이 비용·시간 먼저 지출.
- **비용**: Fargate task 1회(ibex 크기·시간에 비례, aes보다 큼). 마찰 시 D5(정지·보고).

## 옵션 C — 둘 다 (2-fold 지금 + ibex 후 3-fold)

- **내용**: A를 지금, 이어서 B.
- **Pros**: 조기 신호 + 강한 최종 결과 모두.
- **Cons**: B의 비용·시간. 단 A가 먼저라 *ibex 결과 전에 기계·방향을 점검*하는 이점은 유지.
- **비용**: B와 동일.

## 옵션 D — 지금 여기까지

- **내용**: gcd+aes 데이터 확보까지만. 게이트·ibex는 나중에.
- **Pros**: 완전 무지출 정지. 데이터는 남음(언제든 게이트 가능).
- **Cons**: 교차설계 *실측 결과* 없음(이번 작업의 payoff 미수령).

## 추천

**A (2-fold 게이트 먼저)**. 근거: ① 무비용으로 *기계가 실데이터에서 작동*하는지 + *분포-shift 일반화의
방향*을 즉시 확인. ② 그 결과가 ibex 지출 가치를 알려줌 — 예컨대 2-fold가 이미 `generalizes_better`면
ibex로 강화 가치가 크고, `mixed`(분포 shift 지배)면 "더 *비슷한* 설계가 필요한가, 더 *많은* 설계가
필요한가"를 먼저 따져 ibex 외 대안(jpeg 등 또는 다른 PDK)을 고려할 수 있음. ③ "싼 검증 먼저"는 이
프로젝트가 반복 학습한 패턴.

| 옵션 | 비용 | 결과 강도 | 조기 신호 | 추천 |
|---|---|---|---|---|
| A 2-fold 먼저 | 0 | 약(2 fold) | ✅ | ⭐ |
| B ibex 먼저 | AWS $·시간↑ | 강(3 fold) | ✗ | |
| C 둘 다 | AWS $ | 강 | ✅ | 차선 |
| D 정지 | 0 | 없음 | — | |
