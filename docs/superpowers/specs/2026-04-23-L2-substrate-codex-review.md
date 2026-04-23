---
title: L2 Substrate derived spec Codex review log
date: 2026-04-23
target: docs/superpowers/specs/2026-04-23-L2-substrate-design.md
---

# L2 Substrate derived spec — Codex review log

## Design Judgment (pre-review, §3.2 Alternative 선택)

- dispatched: 2026-04-23T20:10+09:00 (read-only sandbox, `< /dev/null` 적용)
- question: §3.2 tier ↔ confidence 매핑 3개 대안 (A 1:1 / B 2차원 / C orthogonal) 중 G2 bootstrap 전 시점에 가장 적합한 선택
- **verdict**: **Pick B.**
- rationale (Codex 원문 발췌):
  > B preserves the existing `tier` contract while adding a defensible, additive claim-strength layer without inventing a new review cadence before G2. A is too lossy: it collapses provenance quality into claim strength and blocks common "independently inferred by multiple sources" nuance. C is conceptually clean, but premature before L1 artifacts exist; κ-weighted confidence needs stable reviewer workflow and enough examples to calibrate.
- promotion gate 차단 기준 (Codex 5개 rule, §3.3 직접 인코딩):
  1. `confidence` cannot be derived reproducibly from bundle metadata
  2. `GOLD` depends on single-source evidence
  3. `AMBIGUOUS` receives any promotion-confidence
  4. source_count/source identity is missing or non-auditable
  5. confidence is used for §5.3 publish/kill decisions rather than only L2 evidence/promotion semantics

spec §3.2/§3.3/§5.2/§5.3은 본 판단에 따라 Alternative B 버전으로 확정됨.

---

## Round 1 — 구조/일관성 (overview §3.2 v2 호환성)

- dispatched: 2026-04-23T20:30+09:00
- findings (판정: **needs-revision**):
  1. `L2.memory.recall` 확장이 **schema 표기상** breaking으로 읽힘. 신규 필드(`source_files`, `source_count`, `last_ingested`, `valid_from`, `age_days`)가 required처럼 선언됨. → **모두 `Optional[...] = None` 또는 default 값으로 명시** + min-required는 parent와 동일하게(`node_id`, `tier`, `source_file`) 재확인.
  2. `tier_weight: AMBIGUOUS=0.0` 주석 "출력 단계에서 이미 제외됨이 정상"이 parent output schema의 AMBIGUOUS 허용을 **좁히는 문구**로 읽힘 → "ranking에서 낮은 우선순위이나 schema상 반환 가능"으로 재표현.
  3. `L2.skill_library.query` 계약 변경 없음 확인 (no action).
  4. §4.2 freshness 90-day warning이 `L2.lint.check()` output schema(`{ok, errors, metrics}`)의 `warnings` 필드로 오해될 여지 → 별도 metric/log로 명시 ("CloudWatch custom metric 또는 stderr warning").
- resolution: 즉시 fix 3건 인라인 적용 (§5.2 output schema · §5.3 tier_weight 주석 · §4.2 lint output 분리 문구).

## Round 2 — 의미 gap 충분성 (tier ↔ confidence 축 분리)

- dispatched: 2026-04-23T20:45+09:00
- findings (판정: **needs-revision**):
  1. §3.1의 `confidence = 주장 강도`가 §5.3 `claim validity`와 충분히 분리되지 않음. "cross-tier confirmed"가 validity gate로 읽힐 여지 → **"evidence support strength (provenance-backed support level)"** 로 rewording + "factual validity 아님" 명시.
  2. §3.2 `EXTRACTED ∧ 1 source → SILVER` row의 "single-source structural match" 전제(auditable source identity 보유 + unique source_count=1)가 문장에 명시 안 됨 → 명시 필요. §3.3 #4와 consistent.
  3. §3.3 #4 "같은 파일의 중복 chunk만 있어 unique source_count = 0" 오류 — 같은 파일 여러 chunk는 unique=1 → "source file identity가 결측된 chunk만 있는 경우"로 정정.
  4. §3.3 #2는 중복이 아니라 방어적 schema rule로 확인 (no additional action).
  5. §1.2와 §3.3 #5 consistent 확인 (no action).
- resolution: 즉시 fix 3건 인라인 적용 (§3.1 언어 분리 · §3.2 SILVER row 전제 명시 · §3.3 #4 정확성 수정).

## Round 3 — H3 falsifier 훼손 여부

- dispatched: 2026-04-23T21:00+09:00
- findings (판정: **needs-revision**):
  1. §6.2가 `≥ 3 model family`만 언급하고 overview §4.3/§5.3/§5.4의 **evaluator N ≥ 5**를 재명시하지 않아 5→3 하향처럼 읽힘 → "5 evaluators selected across at least 3 families, with humans as primary evaluators"로 확정.
  2. §6.1 κ ≥ 0.6의 적용 범위는 §6.4와 결합 시 명확 (L1 sign-off = boolean artifact, L3 evaluator = FM rubric) — no action.
  3. §3.3 #5 "schema-enforceable" 표현이 과함. 실제 input schema 차단 규칙이 없으면 선언에 그침 → "ranking only, canonical decision forbidden"으로 강화하여 **§5.3 decision input에서 `confidence*` 필드 명시적 drop + §5.3 rubric 문구에 해당 용어 금지** 구체화.
  4. §6.3 freeze 대상의 **변경 권한 주체 불명확**. L3가 iteration 중 weight 변경 시 규칙 위반 → "L2 spec-owner 전속, L3 변경 금지, runtime 구현은 read-only 참조만" 명시.
- resolution: 즉시 fix 3건 인라인 적용 (§6.2 N≥5 floor 명시 · §3.3 #5 강제력 명시 3-point · §6.3 변경 권한 + runtime read-only 규칙).

---

## Follow-up fixes summary

Round 1/2/3 합계 **9건 inline fix** 모두 본 spec 파일에 직접 반영. 별도 deferral 없음.

| Round | Fix # | 지점 | 핵심 변경 |
|---|---|---|---|
| R1 | 1 | §5.2 recall output schema | 9개 신규 필드 모두 `Optional[...] = None` 명시 |
| R1 | 2 | §5.3 tier_weight 주석 | AMBIGUOUS schema 반환 허용 표현 |
| R1 | 3 | §4.2 freshness threshold | 90-day warning이 lint output schema에 영향 없음 명시 |
| R2 | 1 | §3.1 축 정의 | "evidence support strength" 용어 채택, factual validity 분리 |
| R2 | 2 | §3.2 SILVER row | auditable source identity 전제 명시 |
| R2 | 3 | §3.3 #4 | unique source_count=0 판정 기준 정확성 수정 |
| R3 | 1 | §6.2 evaluator separation | N≥5 floor × ≥3 families 결합 명시 |
| R3 | 2 | §3.3 #5 | ranking-only + canonical decision input drop 강제 |
| R3 | 3 | §6.3 freeze | L2 spec-owner 전속 변경 권한 + L3 금지 |

## Verdict

- [x] 3 rounds **needs-revision** (no `fail`) — 9 follow-up fixes inline 적용 후 본 spec ship-ready. 그래피파이 adoption spec 선례(Task 6/8 quality-fix 패턴)와 동형.
- [ ] ≥ 1 round `fail` after 3 iterations → spec 재작성 필요 (본 케이스 해당 없음).

## 후속 (본 spec 구현 이슈 candidates)

spec 승인 후 생성 예상:

1. **schema 반영**: `L2.memory.recall` output Pydantic 모델(`src/semi_design_runner/l2_schema.py` 신설), 신규 9 optional 필드 포함.
2. **`scripts/compute_confidence.py`**: alternative B 매핑 구현. `source_count` 계산 + GOLD/SILVER/BRONZE tier 부여.
3. **freshness metadata 주입**: `/graphify --update` hook으로 `last_ingested`/`valid_from`/`valid_to` 필드 ingest.
4. **§3.3 / §5.3 / §6.3 regression test**: `confidence*` 필드가 §5.3 decision input에서 drop되는지 · ranking weight가 runtime에서 read-only인지 assertion.
