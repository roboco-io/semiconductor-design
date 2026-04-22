---
title: graphify 전환 overview spec v2 Codex 3-round review
date: 2026-04-22
target: docs/superpowers/specs/2026-04-19-integrated-research-program-design.md (v2)
---

# Codex 3-round review log

## Round 1 — 구조/일관성 (L2 인터페이스 호환성)
- dispatched: 2026-04-22T14:31+09:00 (재시도, 초기 시도는 동시 프로세스 폭주로 stream disconnect 발생)
- findings (판정: **needs-revision**):
  1. `L2.lint.check()`는 **그래프 구조 무결성**(orphan/dangling/AMBIGUOUS 비율)만 보장하지 `L2.memory.recall()` **반환값 품질**(per-node freshness, source 신뢰도, ranking calibration, `confidence_score` 산식, tier별 소비 규칙)은 보장하지 않는다. 두 인터페이스 사이 품질 gap이 §3.2에서 닫히지 않음.
  2. `skill_library.query()` output schema의 `signed_off_report_uri` ↔ "Min required fields"의 `attached_report_uri` 명칭 불일치. Pydantic 상속 원칙과 충돌하는 작은 계약 불일치.
  3. 하단 "의미 gap 공지"는 문구 수준 경고일 뿐. 소비자 오독 차단을 위해서는 (a) schema 수준에서 `claim_validity`를 `tier`와 별도 필드로 분리하거나 (b) `tier != AMBIGUOUS`만으로 promotion 가능/불가를 **schema-enforceable**하게 선언할 필요.
- resolution: **spec revise needed** — (1) `confidence_score` 정의 gap은 L2 파생 spec으로 deferral 가능(과다 스코프 방지), (2) skill_library 명칭 불일치는 본 spec에서 즉시 정정, (3) 의미 gap 방어 강화는 §7.3 gate 조건이 이미 `tier ∈ {EXTRACTED, INFERRED}`를 강제하므로 §3.2 공지에 해당 강제력을 명시적으로 교차 참조로 보강.

## Round 2 — 의미 gap 설명 충분성 (graphify confidence ≠ 주장 타당성)
- dispatched: 2026-04-22T14:35+09:00 (재시도, stdin이 TTY인 경우 codex hang — `< /dev/null` 리다이렉트로 해결)
- findings (판정: **needs-revision**):
  1. §3.2 `L2.memory.recall()` output에 `confidence_score`가 **잔존**해 v1 의미 부활 우려. graphify tier가 evidence 강도를 전담한다는 §5.2-1·§7.3 선언과 충돌.
  2. §5.3 evidence origin ("tier ∈ {EXTRACTED, INFERRED}인 god-node + human-reviewed claim")에서 **tier의 역할**이 evidence **admissibility** gate인지 claim **validity** gate인지 한 문장 더 분리 필요. "tier는 증거 후보의 추출·연결 품질 gate일 뿐, H1/H3 pass 근거가 아니다"를 §5.3에 직접 명시 권장.
  3. §5.3 R0 precedence에 **역참조**로 "graph integrity/AMBIGUOUS lint fail은 R0 조건이 아님"을 1줄 추가하면 R0 vs §7.3 triage 경계 오독 여지가 더 줄어듦.
- resolution: **spec revise needed** — (1) `confidence_score` 필드 제거(L2 파생 spec에서 필요 시 재도입), (2)(3) §5.3에 tier admissibility 단서 + R0 역참조 1-2줄 추가.

## Round 3 — §5.3 증거 경로 변경이 H1/H3 falsifier를 훼손하지 않는지
- dispatched: 2026-04-22T14:40+09:00 (재시도, `< /dev/null` 적용)
- findings (판정: **needs-revision**):
  1. **H3 evidence bundle 명시 부족**. §5.3은 H1/H2/H3 증거를 "god-node + human-reviewed claim + L1 sign-off report"로 묶지만, H3 falsifier의 핵심은 raw trace/log diff, 평가자 N≥5, Cohen's κ≥0.6, FM1~FM4 판정표다. H3 전용 evidence bundle을 별도 명시해야 falsifier가 훼손되지 않는다.
  2. **§7.3 L3 entry 차단의 cadence 리스크**. AMBIGUOUS>0.3 시 "L3 entry 전체 차단"이 graph 품질 이슈로 H1 실험 시작/반복을 과도하게 막을 수 있다. 차단 범위를 (a) "신규 promotion/L3 실험 착수" vs (b) "진행 중 preregistered run 중단"으로 구분 필요.
  3. H1b 부록 C exclusion은 graphify 기반에서도 검증 가능하나, **최종 판정은 graphify 자동분류가 아니라 frozen Appendix C + 공식문서 parameter 대조 + blinded audit**이어야 한다(부록 C.4 정신 유지 확인).
- resolution: **spec revise needed** — (1) §5.3에 H3 evidence bundle 별도 1-2줄, (2) §7.3 step 6 "진행 중 preregistered run은 차단 대상 아님" 단서 추가, (3) H1b Appendix C 판정 경로는 이미 §5.2-1·부록 C.4와 일관 — 별도 수정 불요.

## Follow-up fixes (Task 8 후속 커밋, Task 6 quality-fix 선례 따름)

아래 8건 중 spec 즉시 적용 6건, 파생 spec deferral 2건:

**즉시 적용 (overview spec §3.2 / §5.3 / §7.3)**:
- F1 (R1-minor): §3.2 `skill_library.query` 출력 `signed_off_report_uri` ↔ min required `attached_report_uri` 명칭 정합.
- F2 (R2-1): §3.2 `L2.memory.recall` output에서 `confidence_score` 필드 제거 (tier가 전담).
- F3 (R2-2): §5.3에 tier의 역할을 "evidence admissibility gate, NOT claim validity" 1줄 명시.
- F4 (R2-3): §5.3 R0 precedence 하단에 "graph integrity/AMBIGUOUS lint fail은 R0 조건이 아님 — §7.3 독립 lint signal로 남는다" 역참조 1줄.
- F5 (R3-1): §5.3에 H3 전용 evidence bundle 1-2줄 — raw trace/log diff + 평가자 N≥5 + Cohen's κ≥0.6 + FM1~FM4 판정표.
- F6 (R3-2): §7.3 step 6에 "preregistered 진행 중 run은 차단 대상 아님. 신규 promotion·L3 entry·신규 실험 착수만 차단" 단서 추가.

**L2 파생 spec deferral (overview scope 밖)**:
- D1 (R1-1): per-node freshness, source 신뢰도, ranking calibration, `confidence_score` 산식, tier별 소비 규칙은 L2 파생 spec에서 정의.
- D2 (R1-3): §3.2 의미 gap 방어는 §7.3 Finding → canonical wiki page gate의 `tier ∈ {EXTRACTED, INFERRED}` 강제로 schema-enforceable하게 이미 반영됨 — §3.2에 교차 참조 주석 1줄만 보강 (F3와 합치).

## Verdict
- [x] 3 rounds **needs-revision** (no `fail`) — follow-up fix 6건 즉시 적용 후 S3 진행 (Task 6 quality-fix 선례와 동형 처리)
- [ ] ≥1 round fail after 3 iterations → S3 진입 금지, spec 재작성 필요
