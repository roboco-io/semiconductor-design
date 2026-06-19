---
title: Codex Review Gate
aliases: [codex-review-gate, codex-review-approval, 검토 게이트]
type: decision
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[gate-chain]], [[generation-log]]
---

# ADR: Codex 검토·승인 게이트 (권력분립)

- **일자**: 2026-06-16
- **상태**: Accepted

## 맥락
검토·승인을 객관화하려면 **생성자 ≠ 판정자**가 코드뿐 아니라 사람 워크플로(spec/plan/code 검토)에도
적용돼야 한다. Claude 자기검토는 공유 맹점 때문에 자기 산출물의 결함을 놓친다.

## 결정
`codex-review-approval` 스킬 도입 — Codex MCP(`mcp__codex__codex`, sandbox=read-only)로 verdict 위임.
verdict 계약: `{verdict: approve|request_changes|block, reasons, must_fix[]}`. 실패/누락 시 보수적 차단.
같은 Codex 구독 인증 → metered 비용 없음.

## 대안
- A안(채택): Codex MCP 객관 판정자. 독립 컨텍스트.
- B안(기각): Claude 자기검토 — 생성자=판정자, 맹점 공유.

## 결과 (3단계 dogfood — 각 단계 고유 결함 적발)
- **spec 단계**: LODO 부분실패 차단 누락을 **block**으로 적발(spec §7이 "fold 실패 → 차단"이라 했으나
  `run_crossdesign_gate`는 부분실패에 통과 verdict) → orchestrator 층 차단으로 수정.
- **plan 단계**: spec 커버리지 갭 3 must_fix(단일설계 LODO 생략 명기·비교성 경고 리포트화·frozen 검사 보강).
- **code 단계**: program.md 게이트 텍스트가 LODO 누락 → 1 must_fix.
- 통찰: 단계마다 고유 결함(spec=의미 갭, plan=커버리지, code=문서-구현 정합)을 표면화.

## 참고
- `.claude/skills/codex-review-approval/SKILL.md`, `.mcp.json` (codex stdio).
