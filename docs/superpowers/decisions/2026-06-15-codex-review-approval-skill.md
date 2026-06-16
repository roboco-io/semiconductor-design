# Decision Brief — Codex 검토·승인 스킬 설계

> 목적: "검토 승인을 객관화하기 위해 Codex MCP를 쓰는 스킬"을 만들기 위한 설계 선택 정리.
> 읽고 결정하면 그대로 구현. 핵심 긴장: 사용자는 *MCP*를 명시했으나 MCP 등록은 *세션 재시작* 후
> 활성화(CLAUDE.md staleness invariant).

## 배경 (사실)

- Codex CLI 0.128.0 설치. `codex mcp-server`(stdio MCP 서버)·`codex exec`(one-shot CLI) 둘 다 가능.
- 기존 자율 루프 Codex 심사관은 **CLI 셸아웃**(`promotion_reviewer.py` + `codex_review_fn`).
  본 스킬은 그것과 별개로 **사람 워크플로(spec/plan/code 검토 게이트)** 를 객관화하는 용도.
- 구독-only 제약: Codex MCP·CLI 모두 동일 Codex 구독 인증 → 추가 과금 0([[project-subscription-only-no-metered-llm]]). 호환.
- 권력분립 원칙: 생성자(Claude) ≠ 판정자. 스킬은 이 원칙을 *사람 검토 게이트*로 확장.

## D1 — Codex 구동 방식

| 옵션 | 내용 | Pros | Cons |
|---|---|---|---|
| **A: MCP 서버 등록** (사용자 명시) | `claude mcp add codex -- codex mcp-server` → `mcp__codex__*` 툴 | 사용자 요청 그대로. 1급 툴 통합. Codex가 repo 파일 직접 read | **이번 세션 미활성**(재시작 필요). 등록·검증을 다음 세션에서 |
| B: CLI 셸아웃 | 스킬이 `codex exec` 호출 | 즉시 동작. 기존 패턴 재사용 | "MCP 아님" — 사용자 명시 위배 |
| C: 둘 다 명시(MCP 우선, CLI fallback) | 스킬 문서가 MCP 사용을 기본으로 하되 미등록 시 CLI fallback 안내 | 사용자 의도(MCP) + 즉시 사용 가능성 | 약간 복잡 |

→ **추천 A** (사용자가 MCP를 명시; 재시작 1회는 staleness invariant상 정상 비용). 등록은 이번 세션,
검증·dogfood는 재시작 후. (C는 "MCP로 객관화" 취지를 흐릴 수 있어 비추천.)

## D2 — 스킬 범위 (검토 대상)

| 옵션 | 내용 |
|---|---|
| **A: spec·plan·code 통합 게이트** | 한 스킬이 산출물 종류를 인자로 받아 적절한 기준으로 Codex 검토 |
| B: spec 검토 전용 | brainstorming의 spec 리뷰 게이트만 객관화 |
| C: code/diff 전용 | 구현 후 코드 변경만 |

→ **추천 A** (검토·승인은 단계 무관 공통 패턴; 산출물 유형별 기준만 다름). brainstorming spec 리뷰,
writing-plans 후 plan 리뷰, subagent-driven 코드 리뷰에 모두 재사용.

## D3 — 판정 출력 계약

- **추천**: Codex가 마지막 줄에 `{"verdict": "approve"|"request_changes"|"block", "reasons": "...",
  "must_fix": [...]}` JSON 1줄. 기존 `promotion_reviewer`의 "마지막 JSON 파싱 + 실패=보수적 block"
  패턴 재사용(게이트 우회 방지). approve만 통과, 그 외는 사유와 함께 Operator/구현자에 반환.

## D4 — 스킬 위치·트리거

| 옵션 | 내용 |
|---|---|
| **A: 프로젝트 `.claude/skills/codex-review-approval/`** | 이 repo 검토 게이트에 맞춤(frozen 계약·INTENT Not 기준 내장) |
| B: 글로벌 `~/.claude/skills/` | 모든 프로젝트 공용(범용 검토) |

→ **추천 A** (본 프로젝트의 frozen·INTENT·spec-권한 기준을 검토 체크리스트에 녹임 — 범용 스킬보다
이 repo에서 훨씬 정확). 트리거: 사용자가 `/codex-review-approval <artifact>` 또는 검토 게이트 도달 시.

## D5 — 즉시 dogfood 대상

- 방금 쓴 `2026-06-12-loop-crossdesign-integration-design.md`(루프 환류 spec)를 첫 검토 대상으로.
  단 D1-A면 *재시작 후* 가능. 재시작 전엔 스킬 문서만 완성.

## 요약 추천

A(MCP 등록) · A(통합 게이트) · JSON 보수적-block 계약 · A(프로젝트 스킬) · 루프 spec을 첫 dogfood.
재시작 1회 필요(MCP 활성화) — 그 전까지 스킬 SKILL.md 작성·MCP 등록까지 완료.
