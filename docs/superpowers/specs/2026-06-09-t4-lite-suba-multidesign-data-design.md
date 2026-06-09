# T4-lite Sub-A — 다설계 데이터 획득 설계

- **status**: approved (Operator brainstorming 승인 2026-06-09, 결정 브리프 추천 묶음)
- **결정 출처**: [decision brief](../decisions/2026-06-09-t4-lite-suba-multidesign-data.md) (D1~D7).
- **프로그램**: T4-lite **Sub-A**(데이터). Sub-B(교차설계 평가 기계)는 구현 완료 — 이 데이터로 실측.
- **scope**: 운영(Fargate 실행, 비용 게이트) + 최소 코드(결합 유틸 + gcd 불변 가드). gcd frozen dataset 보존.

## 1. 동기

Sub-B `run_crossdesign_gate`는 구현됐으나 데이터가 gcd 단일 설계라 LODO 불가. Sub-A는 **2개 설계
(aes, ibex)를 추가 획득**해 gcd+aes+ibex 결합 dataset을 만들고, *실제* 교차설계 일반화를 측정한다.
인프라는 준비됨(`DESIGN` env 파라미터화). AWS 실 과금 → run-task는 Operator 건별 동의(D4).

## 2. 결정 (브리프 확정)

| # | 결정 | 값 |
|---|---|---|
| D1 | 설계 | **aes + ibex** (gcd 포함 총 3, LODO 3 fold) |
| D2 | 실행 | **순차**(한 설계씩 검증) |
| D3 | 통합 | **신규 결합** `experiments/multidesign/dataset.jsonl`(gcd frozen 보존) |
| D4 | 비용 | **건별 Operator 동의**(run-task마다) |
| D5 | 마찰 | **정지·보고**(자동 스킵 금지) |
| D6 | 파서 | **additive + gcd 불변 검증**(파서 변경 시 gcd dataset byte-identical) |
| D7 | 스택 | **재사용→destroy**(실행 직전 상태 확인) |

## 3. 아키텍처

### 3.1 결합 유틸 — `src/prepare_lib/combine.py` (신규, Operator-owned)
- `combine_datasets(paths: list[Path]) -> list[dict]`:
  - 각 설계 `dataset.jsonl`을 읽어 concat. 모든 행이 **동일 스키마**(8 FEATURE_NAMES + post_route_slack_ns
    + group_key) 인지 검증, 아니면 `ValueError`.
  - 설계 간 `group_key`가 서로 다른지 검증(LODO가 성립하도록; 같은 group_key 중복 시 `ValueError`).
  - 행 순서는 입력 순서 보존(결정적).
- CLI: `python -m prepare_lib.combine --in a.jsonl b.jsonl --out experiments/multidesign/dataset.jsonl`.

### 3.2 gcd 불변 가드 (D6) — 테스트
- 파서(`src/prepare_lib`)를 *변경한 경우에만* 발동: gcd report로 prepare.py 재실행 → 산출 dataset이
  `experiments/real-gcd-fargate/dataset/dataset.jsonl`과 **동일**(정렬·필드)함을 검증. 다르면 실패(파서 변경이
  gcd 파싱을 바꿈 = 비교성 위반).
- Sub-A에서 파서 변경이 *불필요*하면(설계 포맷 동일) 이 가드는 회귀 안전망으로만 존재.

### 3.3 운영 런북 (cost-gated, `cdk/DEPLOY.md` 확장)
설계별 절차(순차, D2):
1. **스택 확인/배포**(D7): EdaFlowStack 상태 확인, 없으면 배포.
2. **설계 가용성 확인**: 컨테이너에서 `ls designs/sky130hd/` 또는 run-task 로그로 aes·ibex 존재 확인.
3. **run-task**(D4 — Operator 동의): `DESIGN=aes` → S3 `runs/aes/<RUN_ID>` 적재.
4. **수집·prepare**: S3 → `experiments/real-aes-fargate/` → `prepare.py --design-id aes` → `dataset.jsonl`.
5. **검증**: 행 수·스키마·group_key=aes 확인. 마찰 시 **정지·보고**(D5).
6. ibex 반복(3~5).
7. **결합**(3.1): gcd+aes+ibex → `experiments/multidesign/dataset.jsonl`.
8. **payoff**: `run_crossdesign_gate(gcd-001-winner train.py, pre-gen-001 baseline, multidesign rows)` →
   교차설계 리포트(`experiments/multidesign/crossdesign.md`).
9. **정리**(D7): `cdk destroy`로 비용 종료.

## 4. 데이터 흐름

```
[Fargate run-task DESIGN=aes] → S3 runs/aes → real-aes-fargate/ → prepare.py --design-id aes → aes/dataset.jsonl
[Fargate run-task DESIGN=ibex] → ... → ibex/dataset.jsonl
gcd/dataset.jsonl(기존 frozen) + aes + ibex
  → combine_datasets → experiments/multidesign/dataset.jsonl (group_key: gcd|aes|ibex)
  → run_crossdesign_gate(winner=train.py, baseline=pre-gen-001) → render_crossdesign_report → crossdesign.md
```

## 5. 에러 처리 (D5)

- 설계 flow 실패(run-task non-zero·report 누락·CTS 죽음) → **정지, 에러를 Operator 보고**. 자동 스킵 금지.
- prepare.py가 새 설계 report에서 파싱 실패 → 정지·보고. Operator가 prepare_lib *additive* 수정(D6) 또는 스킵 결정.
- `combine_datasets` 스키마/group_key 불일치 → `ValueError`(결합 중단).
- run-task 비용: 각 실행 전 Operator 동의(D4) 없으면 진행 안 함.

## 6. 테스트

- `combine_datasets`: 2개 합성 jsonl(group_key A/B) → concat·스키마 검증·group_key 분리 확인; 스키마 불일치·중복 group_key → `ValueError`. (합성 fixture, 비용 0.)
- gcd 불변 가드(파서 변경 시): 재생성 dataset == 기존. (파서 무변경이면 skip/안전망.)
- 기존 79 tests green 유지.

## 7. INTENT 정합

- **gcd frozen 보존**(D3·D6): gcd dataset·gen-001~003 비교성 무손상. 파서는 additive만.
- **AWS 실 과금 게이트**(D4): run-task 건별 Operator 동의 — 자율 무인 $ 지출 금지(브리프).
  (구독-only 원칙은 LLM에 적용; AWS는 별개 실비용 — [[project-subscription-only-no-metered-llm]].)
- **마찰 투명**(D5): 침묵 누락 금지 — Learnings("진짜 실행이 마찰을 surface").
- `train.py`·기존 `prepare.py` 계약 무변경(결합 유틸은 신규, 파서는 additive·검증된 변경만).

## 8. 범위 밖 (후속)

- 교차설계 게이트를 auto-promote AND에 편입(데이터 확보 후 별도 결정).
- 4+ 설계 · 통계 검정 승격(방향성 probe → 유의성).
- 설계별 샘플 불균형 정규화.
- SageMaker/병렬 batch 학습(현 순차 유지).
