# auto-gate 통합 (Codex 승격 심사관) + T1-fix 설계

- **status**: approved (Operator brainstorming 승인 2026-06-08)
- **lineage**: 2026-06-08 Codex 프로젝트 리뷰 — (1) T1 nested-split 서술 부정확, (2) 반복 fold 통계 과신,
  (3) auto-gate 미통합(orchestrator가 `run_validation_gate` 미호출, `awaiting_operator`), (4) 코드-문서 정합 격차.
  + 2026-06-08 재피벗(Operator authority → 비전문가 empowerment, 자율 자동 게이트)의 코드 격차 해소.
- **프로그램**: "Trustworthy Automated Research" 로드맵에서 **auto-gate 통합** 단계 (Codex 권고 재정렬:
  T1-fix → auto-gate 우선, T4/T3/T2는 후속). T1(검증 게이트)은
  [2026-06-07-t1-promotion-validation-gate-design](2026-06-07-t1-promotion-validation-gate-design.md).
- **scope**: harness(`src/pipeline/`) — Operator 소유. `train.py`·`prepare.py`·`dataset` frozen 무변경.

## 1. 동기

재피벗으로 INTENT는 "winner 승격은 객관적 자동 게이트가 판정, 사람은 방향·이해"로 바뀌었으나
**코드는 여전히 `awaiting_operator`**(orchestrator.py)로 멈춰 사람 머지를 기다린다 — INTENT와 정면 모순.
이 격차를 닫되, *맹목적 자율*(Not)을 피하기 위해 **사람 자리를 독립 에이전트(Codex)** 가 채운다:
생성자(Claude+Codex) ≠ 판정자(T1 통계) ≠ 승격 심사관(Codex) 의 **권력분립**.

또한 Codex 리뷰가 T1의 nested-split 서술 부정확·통계 과신을 지적했으므로, auto-gate가 신뢰할 수 있는
T1 위에 서도록 **T1-fix를 선결 번들**한다.

## 2. 설계 결정 (Operator 확정)

| # | 결정 | 값 | 근거 |
|---|---|---|---|
| D1 | 승격 판정 | **자동** (median → T1 → Codex) | 재피벗: 사람은 per-winner 게이트 아님 |
| D2 | 게이트 구조 | **T1 하드(통계) ∧ Codex 소프트(의미) — AND** | 둘 중 하나라도 막으면 승격 안 함(보수적) |
| D3 | 사람 대체 | **Codex 승격 심사관** (사람 아님) | 자율 유지 + 권력분립(생성≠판정≠심사) |
| D4 | Codex 심사 권한 | **무결성·안전 + 품질** 차단 가능 | 누수·계약위반·gaming·side-effect + 타당성·과적합 |
| D5 | git 실행 | **완전 무인** — distinguishable ∧ Codex approve → 자동 train.py 덮어쓰기 + commit + tag | 1안(판정자동) + 심사자를 Codex로 → 결과적 완전자율 |
| D6 | Codex 실패/불가 | **block**(승격 안 함) + 사유 로그 | 보수적 기본값 |
| D7 | T1-fix 범위 | frozen 제약상 *재서술 + 견고성*(프로토콜 재건 아님) | train.py가 항상 fold-train을 0.75 내부분할(불변) |
| D8 | 이해가능성 | 세대마다 **튜토리얼식 generation 리포트** 자동 생성 | INTENT 품질기준(이해가능성) |

## 3. 아키텍처 (단위별 책임)

### 3.1 T1-fix — `src/pipeline/validation.py` (선결)
- **`paired_comparison`**: `a`/`b` 길이 불일치 시 `ValueError`(silent zip 절단 방지).
- **서술 정정**: `candidate_fold_maes` docstring·`render_validation_report`에서 "clean K-fold" →
  **"nested resampling(train.py가 fold-train을 내부 0.75 분할; fold-val은 완전 held-out)"** 으로 정정.
  frozen train.py가 항상 내부 분할하므로 모델은 fold-train 100%가 아닌 75%로 학습됨을 명시(verdict는
  paired 대칭이라 유효).
- **통계 caveat**: 리포트에 "반복 K-fold는 train/val 중첩으로 상관 → bootstrap CI·Wilcoxon p는
  *낙관적*(과신 주의)" 한 줄 추가.
- **path_group 견고성**: `score_holdout` 경로의 인코딩 불일치 가능성 주석화(실데이터 단일값이라 현재 무해,
  다설계(T4) 진입 전 재방문 TODO 링크).

### 3.2 Codex 승격 심사관 — `src/pipeline/promotion_reviewer.py` (신규)
- `review_promotion(winner_src, baseline_src, validation_report, *, reviewer_fn) -> dict`:
  반환 `{"approve": bool, "reasons": str}`.
- `reviewer_fn`은 주입형(테스트는 mock). 실제 구현 `codex_review_fn`은 `sdk.py` 패턴 재사용:
  `subprocess.run(["codex", "exec", "--skip-git-repo-check", prompt], timeout=900)`.
- 프롬프트: winner diff + T1 리포트 + 후보 소스를 주고 **JSON 한 줄**
  `{"approve": <bool>, "reasons": "<...>"}` 출력 요청. 심사 항목(D4):
  데이터 누수 · frozen 계약 위반(단일파일·신규의존성·CLI/FEATURE 불변) · metric gaming ·
  수상한 side-effect/네트워크 · 개선 타당성 · 과적합 징후.
- **실패 처리(D6)**: timeout/non-zero/JSON 파싱 실패 → `{"approve": False, "reasons": "Codex 심사 실패: <사유>"}`.

### 3.3 auto-gate 통합 — `src/pipeline/orchestrator.py`
- `run_generation(..., *, baseline_train_py, gate_seeds=(0,1,2,3,4), gate_repeats=10, auto=True,
  reviewer_fn=None)`:
  1. 후보 생성·median 선택(기존).
  2. winner ≠ None이면 **T1**: `run_validation_gate(winner_src, baseline_train_py, rows, ...)`.
  3. `verdict == "distinguishable"`이면 **Codex 심사**: `review_promotion(...)`.
  4. **T1 distinguishable ∧ Codex approve** → `operator_gate.promote(winner_src, baseline, gen_no,
     approved=True)` (자동 commit+tag). 그 외 → 승격 안 함.
  5. `generation.json` status: `promoted` / `rejected_t1`(indistinguishable·worse) / `rejected_codex`.
- **이해가능성 리포트**(D8): 신규 `src/pipeline/report.py`의 `render_generation_report(gen_no,
  ranking, winner, t1_report, codex_verdict, decision) -> str`(순수 함수). orchestrator가 이를 호출해
  `gen-NNN/report.md`로 저장 — 후보 results·median winner·T1 리포트·Codex 판정+사유·최종 결정.
- `auto=False`면 기존 `awaiting_operator` 경로 유지(회귀·테스트 호환).

### 3.4 doc 정합 cleanup (번들 tidy)
- `program.md`: "winner 선택·머지는 항상 사람" → 자동 게이트(median+T1+Codex) 판정으로.
- `PRD.md`: prepare.py placeholder(§FR/구현표) → 구현됨, 잔여 user-flow 라인 배너 정합.
- `src/pipeline/README.md`: skeleton·존재하지 않는 `batch_launcher`/`result_collector` 제거, 실제 모듈 반영.
- `docs/TUTORIAL.md`: 모델 설명 "sklearn Gradient Boosting" → **VotingRegressor(HistGBDT+ExtraTrees)**.

## 4. 데이터 흐름

```
program.md(방향) + dataset
  → candidate_gen (Claude+Codex) → run_all(median) → winner
  → T1 하드 게이트: run_validation_gate(winner vs 현 baseline) → verdict
      ├ indistinguishable/worse → status rejected_t1 (승격 안 함)
      └ distinguishable → Codex 소프트 게이트: review_promotion → {approve, reasons}
            ├ block → status rejected_codex (승격 안 함)
            └ approve → operator_gate.promote(approved=True): train.py 덮어쓰기 + commit + tag
                        → status promoted
  → gen-NNN/report.md (튜토리얼식: 후보·median·T1·Codex·결정)
```

## 5. 에러 처리

- T1 winner fold 실패(inf) → verdict `worse` → 승격 안 함(기존).
- Codex 심사 실패/불가 → `approve=False` → 승격 안 함(D6).
- `promote` git 실패 → 예외 전파 + status 미기록(부분 상태 방지); 호출부가 로그.
- `auto=True`인데 `reviewer_fn=None` → 실제 `codex_review_fn` 사용(CLI 호출); 테스트는 항상 주입.

## 6. 테스트 (TDD)

- **T1-fix**: `paired_comparison` 길이 불일치 `ValueError`; 리포트에 통계 caveat·nested resampling 문구 포함.
- **promotion_reviewer**: mock reviewer_fn으로 approve/block 분기; reviewer가 timeout/JSON깨짐 →
  `approve=False`(실패=block); 프롬프트에 winner diff·T1 리포트 포함 검증.
- **orchestrator auto-gate**(mock gen_fn·mock reviewer_fn·mock/실 T1):
  - distinguishable ∧ approve → status `promoted`, baseline 변경됨(임시 git은 do_git=False로 격리).
  - distinguishable ∧ block → status `rejected_codex`, baseline 불변.
  - indistinguishable → status `rejected_t1`, Codex 미호출, baseline 불변.
  - `auto=False` → 기존 `awaiting_operator` 회귀 유지.
  - `gen-NNN/report.md` 생성·핵심 섹션 포함.
- 기존 59 tests green 유지.

## 7. INTENT 정합

- `train.py`·`prepare.py`·`dataset` frozen 무변경(T1-fix는 harness만; validation은 읽기·임시분할).
- **재피벗 정합**: 자동 게이트가 승격 판정(INTENT What), 사람은 `program.md` 방향·리포트 이해(per-winner 아님).
- **맹목적 자율 금지(Not) 충족**: median+T1+Codex 객관 게이트 + 튜토리얼식 리포트(이해가능성)가 조건.
- trust boundary(holdout exec): Codex 사전 심사로 부분 완화(완전 sandbox는 범위 밖).
- Codex 심사 임계·프롬프트는 이 spec이 정의(INTENT/plan 복사 인용만).

## 8. 범위 밖 (후속)

- 후보 코드 실행 sandbox(network/fs 격리) — 별도.
- 교차 심사(winner 생성자가 Codex면 Claude가 심사) — 독립성 강화, 후속 옵션.
- 병렬 runner(HUGI/Spot) — `run_all` 순차 유지, T4/인프라 단계.
- T4(다설계)·T3(reasoning trace)·T2(자기개선) — 로드맵 후속.
- 생성 실패가 baseline으로 silent 귀결(sdk.py) 회계 — 별도 개선.
