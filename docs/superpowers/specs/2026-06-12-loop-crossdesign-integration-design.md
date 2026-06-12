# 루프 환류 — 교차설계 일반화의 생성·판정·이해 편입 설계

- **status**: approved (Operator brainstorming 승인 2026-06-12)
- **동기 출처**: [probe-3design.md](../../../experiments/multidesign/probe/probe-3design.md) —
  held-out별 최선이 갈림(aes→V1 델타 / gcd→naive / ibex→혼합훈련 winner). 단일 정답 축이 없으므로
  Operator 수동 조합이 아니라 **에이전트가 trade-off를 탐색**하게 루프에 환류한다.
- **선행 결정**: Sub-B spec §8 "교차설계 게이트의 auto-promote 편입은 데이터 확보 후 별도 결정" —
  본 spec이 그 결정(3설계 2,784행 확보 완료).
- **scope**: 루프 구성(파일 5개) 변경. gen-004 *실행*은 범위 밖(spec 승인 후 운영 단계).

## 1. 목적

probe의 발견을 AutoResearch 루프의 3측면에 환류한다:

| 측면 | 변경 | 효과 |
|---|---|---|
| 생성 | 루프 dataset → 3설계 혼합 | 에이전트의 최적화 대상 자체가 일반화 지표화 |
| 판정 | LODO 게이트 AND 추가 | 일반화를 후퇴시키는 winner 차단(gaming 면역층 추가) |
| 이해 | 리포트 LODO 섹션 + program.md 관찰 힌트 | 비전문가가 큰 흐름 추적(H-B 접근성 축) |

## 2. 클래리파잉 결정 (Operator 확정)

| # | 질문 | 결정 |
|---|---|---|
| Q1 | 편입 강도 | **데이터 교체 + LODO 게이트**(생성·판정 양쪽) |
| Q2 | 게이트 조건 | **worse·unverifiable 차단**, generalizes_better·mixed 통과 — 3 fold 저표본에 맞는 보수적 안전망("일반화를 후퇴시키지 않으면 됨") |
| Q3 | program.md 힌트 | **사실 관찰 힌트**(지시 아님) — 전략 선택은 에이전트에 위임(H-A 독창성 보존) |
| — | 게이트 순서 | **median → LODO → T1 → Codex** — LODO(6회 학습, ~분)가 T1(100회 학습, 3설계 데이터에서 ~수십 분)보다 싸므로 fail-fast |

## 3. 구조적 근거 — train.py는 이미 group-aware

`train.py::split()`(frozen)은 group이 2개 이상이면 `GroupShuffleSplit`으로 val을
**설계-분리(group-disjoint)** 분할한다. 따라서 dataset 교체만으로:

- 후보의 `val_mae` = *안 본 설계*에 대한 MAE (selection이 자동으로 일반화 지표화).
- seed가 바뀌면 val로 빠지는 **설계가 바뀜** → 기존 5-seed median selection이 그대로
  **설계 다양성에 대한 강건성 검증**이 된다(harness 무변경).

## 4. 구성요소 (변경 파일 5개, 전부 Operator-owned — frozen 무변경)

1. **`Makefile`** — `loop` 타깃의 `DATASET ?=` 기본값을
   `experiments/multidesign/dataset-3design.jsonl`로 변경.
2. **`src/pipeline/orchestrator.py`** — auto 경로, T1 *앞*에 LODO 게이트 삽입:
   - `run_crossdesign_gate(winner.src_path, baseline_train_py, rows, tempdir)` —
     기존 Sub-B 함수 재사용, fold 작업물은 `tempfile.TemporaryDirectory`(T1과 동일 패턴).
   - verdict ∈ {`worse`, `unverifiable`} → `status="rejected_lodo"`, T1·Codex 생략.
   - verdict ∈ {`generalizes_better`, `mixed`} → T1으로 진행.
   - 테스트 주입용 `lodo_gate_fn=None` 파라미터(기본 `run_crossdesign_gate`).
   - `generation.json`에 `lodo_verdict` 필드 추가.
   - 단일 설계 dataset이 들어오면 `design_fold_splits`가 ValueError → **LODO 게이트는
     dataset의 설계 수 ≥2일 때만 활성**(단일 설계면 기존 체인 그대로, 리포트에 "LODO 생략" 명기).
3. **`src/pipeline/report.py`** — `render_generation_report`에 LODO 섹션 추가:
   `render_crossdesign_report(lodo_res)` 출력을 T1 섹션 앞에 삽입(게이트 순서와 동일하게).
   시그니처: `render_generation_report(gen_no, ranking, winner_id, t1_report, codex_verdict,
   decision, lodo_report=None)` — `lodo_report=None`이면 섹션 생략(하위 호환).
4. **`program.md`** — 두 갱신:
   - 입력 데이터 설명: "dataset은 다설계 혼합일 수 있고(group_key로 구분), 그 경우 train.py의
     val split은 설계-분리 — val_mae는 *안 본 설계* 예측 성능"을 명시.
   - **관찰 힌트 섹션(신설, 지시 아님)**: ① 델타 label(post_route−synth 잔차 학습)은 드리프트가
     안정적인 설계(aes)에서 naive를 37% 이겼으나 드리프트가 자릿수로 다른 설계(ibex)엔 약했다
     ② 혼합 분포 훈련은 절대 스케일 모델의 미관측 설계 전이를 회복시켰다(ibex서 naive 4.3× 격파)
     ③ held-out 설계별 최선 전략이 갈렸다(단일 정답 축 없음). 출처: probe.md/probe-3design.md.
5. **`tests/pipeline/`** — orchestrator 분기 테스트(아래 §7).

## 5. 판정 체인 (최종)

```
median selection (5-seed, 혼합 dataset → 설계 다양성 강건성)
  → LODO 게이트 (3-fold, worse·unverifiable 차단)        [rejected_lodo]
  → T1 통계 게이트 (50-fold paired, distinguishable 요구)  [rejected_t1]
  → Codex 승격 심사관 (의미·gaming 심사)                   [rejected_codex]
  → promote (git tag gen-NNN-best)                        [promoted]
```

## 6. 비교성 · lineage

- gen-004부터 dataset이 `dataset-3design.jsonl`(2,784행)로 바뀌므로 **gen-001~003의 val_mae와
  직접 비교 금지** — 세대 리포트와 본 spec에 명기. lineage는 `generation.json`의 `dataset`
  필드가 기록(ERD `GENERATION → DATASET` 그대로).
- baseline(현 train.py = gen-001 winner)은 게이트에서 *같은 새 dataset*으로 paired 비교되므로
  게이트 유효성은 dataset 교체와 무관하게 유지.
- 2설계 `dataset.jsonl`·gcd `dataset.jsonl`은 frozen 유지(probe·과거 세대 재현성).

## 7. 에러 처리 · 테스트

- LODO fold 실패(inf) → `unverifiable` → 보수적 차단(`rejected_lodo`). 침묵 통과 금지.
- 테스트(전부 fake gate 주입, 실학습 없음):
  - LODO `worse` → `rejected_lodo`, T1·Codex 미호출, generation.json에 `lodo_verdict` 기록.
  - LODO `mixed` + T1 `distinguishable` + Codex approve → `promoted`(전체 체인 통과).
  - LODO `unverifiable` → `rejected_lodo`.
  - 단일 설계 rows → LODO 생략, 기존 체인 동작(하위 호환).
  - `render_generation_report`의 LODO 섹션 유/무 렌더.
- 기존 94 tests green 유지. Makefile·program.md는 코드 외 — gen-004 실측에서 검증.

## 8. INTENT 정합

- **frozen 무변경**: train.py·prepare.py·기존 dataset 불변. dataset *교체*는 계약(`--data` 인자)
  내부의 운영 결정이며 ERD가 lineage를 기록.
- **맹목적 자율 금지**: 게이트가 하나 *추가*되어 자율 승격의 신뢰가 강화됨(LODO는 T1이 못 보는
  일반화 축을, Codex는 통계가 못 보는 의미 축을 차단 — 3중 권력분립).
- **사전 고정 판정**: 게이트 조건(worse·unverifiable 차단)을 gen-004 실행 전에 본 spec에 고정.
- **비전문가 이해가능성**: 세대 리포트에 LODO 표 추가 — Operator가 "안 본 설계에서도 나아졌나"를
  표 하나로 추적.

## 9. 범위 밖 (후속)

- gen-004 실제 실행(승인 후 운영 — LLM 구독 사용량 소모, AWS 불필요).
- 4번째 설계 추가, LODO 통계 검정 승격(설계 수 확보 후), 설계별 샘플 불균형 가중.
- (연기) reasoning trace.
