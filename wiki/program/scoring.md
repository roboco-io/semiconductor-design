---
type: program-rules
title: "평가·승격 기준 (scoring.md)"
date: 2026-04-19
status: active
related_spec: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md#5
---

# scoring.md — 평가·승격 기준

Candidate · patch · finding · skill의 평가·승격 기준을 overview spec §5와 정렬해 운영 수준에서 기술한다.

## Overview spec 참조 (single source of truth)

- **§5.1 Layer별 지표** — H1a/H1b/H1c · L2 보조 · L1 operational
- **§5.2 Measurement safeguards** — freeze-before-experiment, exclusion list (부록 C), blinded audit, evaluator separation, pre-registration
- **§5.3 Canonical Decision Table** — publish / reframed-publish / kill 결정 (모든 게이트·리스크가 참조하는 유일한 기준)
- **§5.4 Acceptance Thresholds Summary** — 모든 hypothesis threshold 한 표에
- **부록 C.1~C.4** — Gemmini/Chipyard knob exclusion list (H1b 판정용)

## Candidate 평가 출력 스키마

각 `L1.run(spec_uri)` 결과 artifact에는 다음 필드를 포함:

| 필드 | 타입 | 설명 |
|---|---|---|
| `run_id` | ULID | 유일 식별자 |
| `sign_off_status` | enum | `clean` / `drc_fail` / `lvs_fail` / `sta_fail` / `tool_crash` |
| `metrics` | object | `area_um2`, `power_mw`, `max_freq_mhz`, `runtime_s`, `wns_ns`, `tns_ns` |
| `cost_usd` | number | AWS 청구 기준 |
| `reports[]` | list<URI> | `.rpt / .def / .sdc` 파일 경로 (L1 bundle 불변 원칙 — overview spec §3.2) |
| `provenance_uri` | URI | license matrix + artifact lineage (overview spec §13) |
| `lockfile_sha` | string | 사용된 `lockfile.yaml` 스냅샷 hash (overview spec §6.2) |

## Finding 생성 기준

- run 결과가 기존 findings와 `L2.lint.check()`로 매칭되지 않고
- blinded audit (또는 운영자 리뷰)에서 **새 패턴**이라 판정되면
- `wiki/findings/<YYYY-MM-DD>-<slug>.md` 경로에 저장. frontmatter: `confidence`, `last_verified`, `evidence_urls[]`, `derived_from_hypothesis`, `run_ids[]` 필수.

## Failure 생성 기준

- `sign_off_status != clean` 또는 blinded audit fail
- `wiki/failures/<YYYY-MM-DD>-<slug>.md`에 저장. 삭제 금지 (R3).
- frontmatter는 finding과 동일 필드 + `failure_mode` (예: `drc_m2_spacing`, `sta_setup_hold`).

## Skill 승격 기준 (skill library 등록)

- Skill은 `L2.skill_library.query()`를 통해 append-only.
- 새 skill 등록 조건:
  1. 최소 seed × 3 재현 통과
  2. Signed-off report가 attached
  3. Blinded audit N≥2 pass
  4. Skill 설명이 "어떤 디자인 패턴·제약 상황에서 적용 가능한가"를 명시
- Rename / remove 금지. Deprecation은 `status` 필드로만 (overview spec §3.2).

## 평가 무결성 (R0 override 연계)

§5.3 R0 precedence rule은 evaluator separation 위반 · audit 실패 · FM pass율 < 50% · 평가자 N<5 중 어느 하나라도 발생하면 해당 실험 회차의 모든 candidate 평가를 무효 처리한다. 이 경우 publish/reframed/kill 결정 불가 — 실험 무결성 복구 후 재실행.
