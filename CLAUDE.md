# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**2026-08-25 완전 제로베이스 재피벗** — 구 사이클(바이브 코딩 INTENT + H1.1 스모크)을 전량
제거하고 EDA 영역 literature survey부터 재시작했다.

현 프로젝트: **범용 코딩 에이전트의 EDA 하네스 설계 연구** —
FluxBench(2026)가 실증한 "하네스 아키텍처 86% 성능 격차"의 설계 원리 공백을 공략.

- **방향 문서**: [`research-tree.yaml`](research-tree.yaml) (가설 트리) +
  [`research-log.md`](research-log.md) (타임라인)이 프로젝트 상태의 원천.
- **Survey**: [`literature/survey.md`](literature/survey.md) (5축 46편, raw는 `literature/raw/`).
- **가설**: H1 하네스 설계(주축, **protocol LOCKED** —
  [`experiments/H1-harness/protocol.md`](experiments/H1-harness/protocol.md)),
  H1.1 Token ROI(부속), H2 교차 엔진 검증·H4 sign-off 해리(순차 대기),
  H5 학습 축 N=1(경량 병행), H3 REVISE, H6 DEFER. 결정 이력:
  [`issues/001`](issues/001-hypothesis-judgment-brief.md).
- **H1 실행 규율**: pre-flight(환경·태스크·채점기·하네스 커밋)는 기한 미기산.
  **7일 기한은 "실행 개시" 커밋(첫 에이전트 세션 직전)부터.** 개시 커밋 전 실험 조건의
  RTL/결과물 생성 금지 — git 순서가 사전등록 증명. plan 커밋과 results 커밋 절대 병합 금지.
- 가설 정식화 도구: `.claude/skills/meta-research/` — `/meta-research`로 호출.

## 이전 사이클 참조 (main에 없음)

| 자산 | 위치 |
|---|---|
| 직전 사이클(바이브 코딩 INTENT·H1.1 스모크 protocol) | git tag `archive/pre-eda-zerobase-pivot-2026-08-25` |
| EDA surrogate 사례 연구 1 스냅샷 | git tag `archive/pre-vibe-pivot-2026-08-23` |
| 3-layer 시절 자산 | branch `archive/integrated-program-3layer` |
| git 미추적 실험 아티팩트 1.9GB | `~/Backups/semiconductor-design-experiments-2026-08-23.tar.gz` |

이전 사이클 자산을 새 작업의 근거로 삼지 않는다. 필요 시 참조만.

## Intent Constraints (INTENT.md Not 연동 — 2026-08-25)

- **검증은 소프트웨어 우선**: 판정은 시뮬레이션·형식 등가성·로컬 sign-off로 한다.
  실칩 제작(Tiny Tapeout)은 최종 실무성 마일스톤 1회에 한정 — 사이클 게이트에
  하드웨어 제작·비용 지출을 넣지 않는다.

## Code Conventions

- **Direct commits to `main`** (Operator 워크플로우). Conventional commit prefix
  (`docs:` `chore:` `feat:` `test:`), subject는 명령형.
- 설계 fork·열린 결정은 spec에 인라인하지 말고 `issues/`에 파일로.

## Operating Invariants (이전 사이클에서 검증된 메타 패턴 — 유지)

- **웹 조사는 exa MCP** (`web_search_exa`/`web_fetch_exa`). Perplexity는 2026-08-22부로
  제거 — 사용 금지. 응답 수신 직후 first check = citation 개수. citation 0 → 전체 거부 후 재조회.
- **추측 vs grep 검증**: 정합 작업 전 반드시 grep으로 사실 확인. 추측을 기록물에 남기지 않는다.
- **Agent definition staleness**: `.claude/agents|skills|settings` 변경 직후 같은 세션에서는
  활성화되지 않는다 — 세션 재시작 후 재호출이 default.
- **사전 고정 판정**: 판정 기준은 결과 확인 전 고정, 사후 변경 금지. 생성 엔진 ≠ 심사 엔진
  (Codex 게이트 스킬 `.claude/skills/codex-review-approval/` 유지).
- **맹목적 자율 금지**: 객관적 게이트 없이 자율 머지하지 않는다.
