# Decision Brief — T4-lite Sub-A: 다설계 데이터 획득 (AWS Fargate)

> 목적: 선택을 위한 정보. 각 결정마다 옵션·상세·pros·cons·추천. 읽고 결정하면 spec으로 옮긴다.
> (추천은 참고 — 다른 선택도 유효. 실제 Fargate 실행은 비용 게이트로 Operator 명시 동의 후에만.)

## 배경 (grounding, grep 확인)

- `docker/eda-flow/entrypoint.sh`: `DESIGN` env → `make DESIGN_CONFIG=./designs/sky130hd/${DESIGN}/config.mk`
  → 두-시점 `report_checks`(synth.rpt·route.rpt) → S3 `runs/${DESIGN}/${RUN_ID}`. report 포맷은 설계 무관
  동일(minimal, `-fields` 없음 = prepare.py 파서 계약).
- 실행 = `aws ecs run-task` one-shot(`cdk/DEPLOY.md`, "Operator 전용 — 비용 발생", 완료 후 `cdk destroy`).
- `prepare.py --design-id <d>`가 설계별 dataset에 `group_key=d` 스탬프. `train.py`는 group≥2면 design-disjoint.
- 현재 gcd 53행(`experiments/real-gcd-fargate/`)만 존재. Sub-B 교차설계 게이트(`run_crossdesign_gate`)는 구현 완료.
- **목표**: 2~3개 설계 데이터를 더 확보 → 결합 dataset → 실제 교차설계 일반화를 측정(Sub-B 게이트로).

## 결정 D1 — 어떤 설계, 몇 개

**무엇을 정하나**: LODO fold 수(=설계 수)와 다양성. 설계 정확 가용성은 docker 이미지 ORFS sky130hd 세트에
의존(표준: gcd·aes·ibex·jpeg·riscv 등 — 실행 시 `ls designs/sky130hd/`로 확정).

### 옵션 1-A. +1 설계 (aes) → 총 2
- **Summary**: gcd + aes. LODO 2 fold.
- **Pros**: 최소 비용·마찰. 교차설계 *기계* 첫 실증엔 충분(2 설계로 LODO 작동 확인).
- **Cons**: fold 2개 = 방향성 probe가 가장 약함(설계 1개가 결과 좌우). 일반화 주장 매우 제한적.

### 옵션 1-B. +2 설계 (aes, ibex) → 총 3 — 추천
- **Summary**: gcd + aes + ibex. LODO 3 fold. ibex(RISC-V 코어)는 endpoint 多 → 샘플 풍부.
- **Pros**: 다양성(소형 gcd·중형 aes·대형 ibex) → 일반화 probe 의미 있음. 샘플 수도 크게 증가(within-design 통계도 개선). 결정 브리프 D2(probe)와 잘 맞음.
- **Cons**: ibex flow는 오래·비싸고 마찰 위험↑(큰 설계 = CTS·route 시간↑). $ 중간.

### 옵션 1-C. +3 설계 (aes, ibex, jpeg) → 총 4
- **Summary**: LODO 4 fold.
- **Pros**: probe 가장 강함. 향후 통계 검정으로 승격 여지.
- **Cons**: $·마찰 최대. lite 범위 초과 느낌. 한 설계라도 실패하면 일정 흔들림.

**추천: 1-B (aes + ibex, 총 3)** — 다양성·샘플·비용의 균형. LODO 3 fold로 방향성 probe가 처음으로 의미 있어짐. **함의**: ibex 마찰 가능성은 D2(순차)·D5(마찰 처리)로 흡수.

## 결정 D2 — 실행 전략

### 옵션 2-A. 순차 (한 설계씩) — 추천
- **Summary**: aes run-task → report·prepare 검증 → ibex run-task → 검증. 한 번에 하나.
- **Pros**: 설계별 마찰을 *조기 격리*(gcd는 5회 deploy iter 마찰 겪음). 디버그 쉬움. 동시 $ 최소.
- **Cons**: wall-clock 느림(설계 직렬).

### 옵션 2-B. 배치 (병렬 run-task)
- **Pros**: 빠름.
- **Cons**: 마찰이 한꺼번에 터짐. 디버그 어려움. 동시 $↑. gcd 경험상 위험.

**추천: 2-A (순차)** — gcd의 마찰 이력이 "한 번에 하나, 검증하며" 를 강하게 지지.

## 결정 D3 — 데이터 통합

### 옵션 3-A. 신규 결합 dataset `experiments/multidesign/dataset.jsonl` — 추천
- **Summary**: 설계별 prepare.py 출력을 concat(각 행 group_key로 구분). gcd `real-gcd-fargate/`는 그대로 보존.
- **Pros**: train/validation이 단일 파일 읽음(group_key 이미 존재). gcd frozen dataset 무손상(gen-001~003 비교성 유지). 명확.
- **Cons**: 결합 스크립트(간단) 필요.

### 옵션 3-B. 설계별 파일 유지, 로드 시 결합
- **Pros**: 원본 분리.
- **Cons**: 로더 plumbing↑. 이점 적음.

**추천: 3-A (신규 결합 dataset)** — gcd frozen 보존 + 단일 파일. gcd 행은 기존 dataset 재사용(재실행 불필요).

## 결정 D4 — 비용 게이트 & 예산

### 옵션 4-A. plan까지 무비용, run-task는 설계별 Operator 명시 동의 — 추천
- **Summary**: brainstorm·spec·plan은 비용 0. 각 Fargate run-task 직전 Operator가 "실행" 명시 승인.
- **Pros**: 외부·비가역·비용 액션을 건건이 게이트(프로젝트 원칙). 예상 비용도 그때 제시.
- **Cons**: 실행 단계마다 확인 절차.

### 옵션 4-B. 예산 상한 사전 승인 후 자동 실행
- **Pros**: 매끄러움.
- **Cons**: 무인 $ 지출 위험. AWS 비용은 LLM 구독과 달리 실 과금.

**추천: 4-A (건별 동의)** — AWS는 실 과금이라 run-task마다 명시 동의가 안전.

## 결정 D5 — 설계별 flow 마찰 처리

### 옵션 5-A. 시도 → 마찰 시 정지·Operator 보고 — 추천
- **Summary**: 설계 실행이 실패/report 이상이면 멈추고 에러를 Operator에 보고. Operator가 수정(prepare_lib 파서·config) 또는 스킵 결정.
- **Pros**: 침묵 누락 방지. gcd식 마찰(F1/F3 파서·CTS)을 의식적으로 다룸. 데이터 무결성.
- **Cons**: 자동 진행 아님(사람 판단 개입).

### 옵션 5-B. 실패 설계 자동 스킵
- **Pros**: 진행 멈춤 없음.
- **Cons**: 침묵 under-coverage. 어떤 설계가 왜 빠졌는지 흐려짐.

**추천: 5-A (정지·보고)** — 데이터 품질이 일반화 결론의 토대. 마찰을 드러내는 게 프로젝트 가치(Learnings).

## 결정 D6 — prepare_lib 파서 일반화 (frozen 미묘점)

**맥락**: `prepare.py`/`src/prepare_lib`는 *에이전트에게* frozen(공정 비교). Operator는 소유(gcd의 F1/F3 파서
수정도 Operator-side). 새 설계가 파서 quirk를 surface하면 Operator가 고칠 수 있다 — 단 **gcd dataset이 바뀌면
gen-001~003 비교성이 깨진다**.

### 옵션 6-A. 파서 수정은 *additive*, gcd dataset 불변 검증 — 추천
- **Summary**: 새 설계 포맷을 처리하되 gcd 파싱 결과는 byte-identical 유지. 파서 변경 후 gcd dataset 재생성해
  기존과 동일함을 테스트로 확인.
- **Pros**: gcd frozen 비교성 보존. 안전.
- **Cons**: 파서 변경 시 회귀 검증 1단계 추가.

### 옵션 6-B. 파서 자유 변경 + 전 설계 재생성
- **Pros**: 단순.
- **Cons**: gcd dataset 변동 → gen-001~003·gen-001-best 비교 무효화. 큰 부작용.

**추천: 6-A (additive + gcd 불변 검증)** — frozen 환경의 비교성은 프로젝트 핵심(공정 비교). 깨면 H-A 근거가 흔들림.

## 결정 D7 — 스택 수명주기

### 옵션 7-A. 기존 EdaFlowStack 재사용(필요시 재배포) → 실행 → `cdk destroy` — 추천
- **Summary**: 스택 상태 확인(이전 메모: idle ~$0). 없으면 배포, run-task, 완료 후 destroy로 비용 정리.
- **Pros**: 비용 최소화. DEPLOY.md 절차 그대로.
- **Cons**: 배포/정리 절차 오버헤드.

**추천: 7-A** — 실행 직전 스택 상태부터 확인.

## 범위·성공 기준 (확인용)

- **Sub-A 산출**: aes·ibex(추천) report → prepare.py → `experiments/multidesign/dataset.jsonl`(gcd+aes+ibex 결합).
- **payoff**: 결합 dataset에 `run_crossdesign_gate`(Sub-B) 적용 → *실제* 교차설계 일반화 리포트(gen-001 winner vs baseline).
- **범위 밖**: 교차설계 게이트의 auto-promote 편입(별도) · 4+ 설계 · 통계 검정 승격.

## 요약 — 추천 묶음

| 결정 | 추천 | 한 줄 이유 |
|---|---|---|
| D1 설계 | aes + ibex (총 3) | 다양성·샘플·비용 균형, LODO 3 fold |
| D2 실행 | 순차 | gcd 마찰 이력 → 한 번에 하나 |
| D3 통합 | 신규 결합 dataset | gcd frozen 보존 + 단일 파일 |
| D4 비용 | 건별 Operator 동의 | AWS 실 과금 |
| D5 마찰 | 정지·보고 | 침묵 누락 방지, 데이터 품질 |
| D6 파서 | additive + gcd 불변 | 비교성(frozen) 보존 |
| D7 스택 | 재사용→destroy | 비용 최소 |

이 묶음대로 가도 좋고, 개별 결정을 바꿔도 된다.
