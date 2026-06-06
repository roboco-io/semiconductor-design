# 다중 seed median selection harness 설계

- **status**: approved (Operator brainstorming 승인 2026-06-06)
- **lineage**: gen-002 실행에서 단일 seed=0 선택이 위양성 winner를 뽑은 문제(아래 §1)
- **scope**: harness(`src/pipeline/runner.py` · `selection.py` · `orchestrator.py`) — Operator 소유.
  `train.py`(frozen 계약) · `prepare.py`(frozen 평가 데이터) **무변경**.

## 1. 동기 (negative result)

gen-002 winner(codex, moderate)는 harness 기준 seed=0에서 `val_mae=0.0992`로
baseline(gen-001 winner, 현 `train.py`, seed0 `0.1042`)을 이겨 winner로 선택됐다.
그러나 다중 seed(7-seed: 0,1,7,13,42,123,777) 재검증에서:

| 지표 | baseline | gen-002 winner | 판정 |
|---|---|---|---|
| mean val_mae | 0.0928 | 0.0959 | baseline 우세 |
| median val_mae | 0.0799 | 0.0992 | baseline 우세 |
| 이긴 seed | 4/7 | 3/7 | baseline 우세 |

→ **단일 seed 선택이 53샘플·random split의 운에 좌우돼 일반화되지 않는 winner를 뽑았다.**
이는 OD-5(데이터 한계, `issues/003`·`issues/005`)가 selection 프로토콜로 전파된 것이며,
"에이전트가 baseline을 능가"(H-A)가 단일 seed에서는 위양성일 수 있음을 보여주는 연구 산출물이다.
H-B(Operator 게이트)가 이 위양성 승격을 막았다.

## 2. 설계 결정 (Operator 확정)

| # | 결정 | 값 | 근거 |
|---|---|---|---|
| D1 | 집계 통계량 | **median** | outlier split에 강건, 노이즈 환경에 적합 |
| D2 | seed 개수 | **5개 고정 `(0,1,2,3,4)`** | median 안정성 ↔ 실행시간 균형, 재현성 |
| D3 | inf 처리 | **하나라도 inf면 후보 탈락** | "재현·안정 코드만 승격" + 현 fail=lose 철학 계승 |
| D4 | per-seed 기록 | **results.tsv에 seed별 값 보존** | 노이즈·위양성 사후 감사, 연구 투명성 |

## 3. 아키텍처 (단위별 책임)

### 3.1 `runner.run_candidate_multiseed(train_py, dataset, out_dir, seeds=(0,1,2,3,4))` — 신규
- 각 seed로 기존 `run_candidate`를 호출 → `vals: list[float]` 수집.
- **단락(short-circuit)**: 어떤 seed가 `inf` → 즉시 `inf` 반환(나머지 seed 평가 생략, D3).
- 전부 유한 → `(statistics.median(vals), vals)` 반환.
- `seeds`는 인자 주입 가능 → 재현성 + 테스트 결정성.

### 3.2 `runner.run_all(candidates, dataset, out_root, seeds=(0,1,2,3,4))`
- `seeds` 파라미터 추가, 내부적으로 `run_candidate_multiseed` 경유.
- 반환을 `(candidate, median_val, per_seed_vals)` 3-튜플로 확장.
- **하위호환**: 단일 seed 호출 시 `median([x]) == x`. 기존 `seed: int=0` 시그니처는
  `seeds=(seed,)`로 흡수하거나 deprecate (테스트가 깨지지 않는 쪽 선택).

### 3.3 `selection.select_winner(results)` — 인터페이스 무변경
- 입력 튜플의 1번 인덱스(median_val) 기준 정렬·최저값 winner. 로직 동일.
- per_seed_vals(2번 인덱스)는 selection이 무시하고 통과시킴(orchestrator가 기록용 사용).

### 3.4 `orchestrator.run_generation(...)`
- `seeds`를 `run_all`에 전달.
- `results.tsv`에 `median_val_mae` + `per_seed_vals`(JSON 컬럼) 기록(D4).
- `generation.json`에 `eval_seeds: [0,1,2,3,4]` · `metric: "median_val_mae"` 기록(프로토콜 출처 명시).

## 4. 데이터 흐름

```
candidates
  → [seed∈{0,1,2,3,4}: train.py subprocess]   (각 seed별 val_mae)
  → run_candidate_multiseed: inf 단락 OR median
  → run_all: (cand, median, per_seed[])
  → select_winner: 최저 median winner
  → results.tsv (median + per_seed JSON) + generation.json (eval_seeds, metric)
```

## 5. 에러 처리

- subprocess non-zero/timeout/무출력 → 해당 seed `inf`(기존 `run_candidate` 동작).
- 후보의 어느 seed든 `inf` → 후보 `inf`(D3) → selection이 패배 처리.
- 전 후보 `inf` → winner `None`, `winner_val_mae: null`(기존 동작 보존).

## 6. 테스트 (TDD, 구현 전 작성)

- `median` 집계 정확성(홀수 개 → 중앙값).
- inf 단락: 한 seed inf면 후보 inf, 나머지 seed subprocess 미호출(mock call count).
- 단일 seed 하위호환: `median([x]) == x`, 기존 39 tests green.
- 고정 seed 재현성: 같은 seeds → 같은 ranking(결정성).
- per-seed 기록: results.tsv에 seed별 값 직렬화/역직렬화.

## 7. INTENT 정합

- `train.py` frozen 계약(`--data/--out/--seed`·8 FEATURE_NAMES·stdout `{"val_mae"}`) **무변경** — seed는 이미 CLI 인자.
- `prepare.py`·dataset 스키마 **무변경**.
- 변경은 harness(Operator 소유)뿐 → "에이전트는 train.py 단일 파일만 변형" 비저촉.
- 고정 seed 리스트 → "세대 간 결과 재현(동일 데이터셋·lockfile_sha)" 품질 기준 강화.
- 집계 *방법*만 정의, 정량 임계값 재정의 없음 → "INTENT/plan은 spec 임계값 복사 인용만" 준수.

## 8. 재판정 계획 (harness 완성 후)

1. gen-002 후보(`experiments/gen-002/candidates/cand-00{0,1}`)를 새 harness로 `[0,1,2,3,4]` 재평가.
2. 현 baseline(`train.py`) median과 비교.
3. 결과를 Operator에 보고 → **승격 판단은 여전히 Operator 게이트(H-B)**. 자율 머지 없음.
4. (예상) §1 분석상 baseline 우세 → gen-002 status `rejected`, gen-001 baseline 유지.
   negative result는 INTENT.md Learnings에 co-evolution 신호로 기록.
