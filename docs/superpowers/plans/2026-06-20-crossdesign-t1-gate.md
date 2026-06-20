# Plan — 교차설계 repeated-LODO T1 게이트 구현 (2026-06-20)

spec: `docs/superpowers/specs/2026-06-20-crossdesign-t1-gate-design.md` (§ 참조). TDD, 각 task는
red→green. frozen 계약(train.py/prepare.py/dataset) 무변경 — validation.py·orchestrator.py·report만.

## Task 1 — split 3-tuple 호환 + `repeated_design_fold_splits` (validation.py)
spec §3.1·§3.2. **TDD**: `tests/pipeline/test_validation.py`에 추가.
1. **red**: `repeated_design_fold_splits(groups, repeats=10, base_seed=0)` 테스트 — D=3, repeats=2 →
   6 fold, 각 `(tr, va, seed)`. held-out 설계별 va 인덱스 정확, seed=base_seed+r, D<2 → ValueError.
   - **결정적 순서 가드**: *비정렬* group 레이블(예: `["b","a","b","c","a"]`)을 넣어도 fold 순서가
     `sorted(set(groups))`(=`["a","b","c"]`)를 따름을 assert(spec §3.1 sorted-unique).
2. **red**: `naive_fold_maes`가 3-tuple split에서 `va=split[1]` 사용(seed 무시), 2-tuple도 동작.
3. **red**: `candidate_fold_maes`가 3-tuple seed를 `run_candidate`에 전달, 2-tuple → seed=0
   (run_candidate를 spy mock으로 호출 seed 검증).
4. **green**: 세 함수 구현/확장. 2-tuple/3-tuple 분기는 `len(split)`로.

## Task 2 — `run_crossdesign_validation_gate` + 리포트 scheme 분기 (validation.py)
spec §3.3·§3.5·§4. **TDD**: 같은 테스트 파일.
1. **red**: 게이트가 `repeated_design_fold_splits`로 fold 생성, winner/baseline/naive paired 평가,
   `verdict()` 재사용. 반환 dict에 `scheme="repeated_design_lodo"`, `repeats`, `n_designs`.
   - winner 또는 baseline 한 fold라도 inf → `verdict_vs_baseline="worse"`(회귀 가드).
   - distinguishable 케이스(winner 유의 낮음) → "distinguishable".
2. **red**: `render_validation_report`가 `scheme == "repeated_design_lodo"`일 때 교차설계 제목/상관
   caveat 출력(단일설계 경고 대신). 그 외/scheme 부재 → 기존 혼합 T1 리포트(회귀 가드). 정확한 scheme
   값으로 분기(키 존재만으로 분기 금지 — 미래 scheme 오분류 방지).
3. **green**: 게이트 함수 + 리포트 분기 구현. `alpha=0.05`, `repeats=10` 기본값(spec §4).

## Task 3 — orchestrator 분기 (orchestrator.py)
spec §3.4. **TDD**: `tests/pipeline/test_orchestrator.py`.
1. **red**: 다설계(≥2 group_key) + LODO 통과 시 T1이 `run_crossdesign_validation_gate`로 호출됨
   (주입 mock으로 확인). 단일설계 → 기존 `run_validation_gate`.
2. **green**: `run_generation`의 T1 호출부를 다설계/단일설계로 분기. `gate_fn` 주입은 유지(기본값만 분기).
3. 기존 auto 테스트(`_stub_lodo("mixed")` 등) 회귀 없음 확인.

## 검증 (전 task 후)
- `make test` 전체 green, `make lint` clean.
- **gen-006 winner 재평가 (필수, spec §7)**: `experiments/gen-006/candidates/cand-001/train.py`를 새
  교차설계 T1 게이트로 baseline 대비 재평가하고 verdict를 기록 — 기존 혼합-T1의 `worse`와 *다를 수
  있음*(교차설계축 측정 확인). 결과를 experiments/gen-006에 메모로 남김.
- 최종 diff를 Codex 검토 게이트(code 기준)로 판정 후 커밋.

## Not
- LODO 방향성 게이트(`run_crossdesign_gate`) 무변경.
- 임계값은 spec §4만 single source — plan에서 재정의 없음(인용만).
- 2차 harness 갭(ast.parse)은 별도 작업(이 plan 범위 밖).
