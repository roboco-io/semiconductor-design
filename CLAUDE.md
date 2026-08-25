# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**2026-08-22 완전 피벗(원점 재시작)** — 이전 프로젝트(EDA surrogate 사례 연구 1 + 거버넌스
일반화)는 전부 내려놓고 의도 정의부터 다시 시작했다.

새 프로젝트: **반도체 설계 × 바이브 코딩** —
"AI를 활용해 비전문가 소프트웨어 개발자가 학습과 반도체 설계를 하나의 사이클로 계속
진화시켜 나갈 수 있는가"를 실험. 결과는 객관적으로 검증·측정 가능하고 실무 사용 가능해야 한다.

- **[`INTENT.md`](INTENT.md)가 유일한 방향 문서** (status: exploring). Why는 확정,
  확인 방법은 이중 축으로 결정(2026-08-22, [`issues/011`](issues/011-intent-verify-method-selection.md)):
  - 설계 축: 기능 정합(pass@k·형식 등가성) + METRICS2.1 기반 PPA/sign-off 게이트
  - 학습 축: DLCI pre/post + AI 상호작용 패턴 로그 (성과-학습 해리 대응, 분리 측정)
  - 실무성 마일스톤: Tiny Tapeout 실리콘 실증
- What(난이도 사다리 + 한계 지도, 사이클 = 설계→튜토리얼→서술형 퀴즈→이중 축 게이트,
  [`issues/012`](issues/012-intent-what-candidates.md))·Not(소프트웨어 검증 우선) 작성 완료.
  열린 `(?)`: 서술형 퀴즈 채점의 객관성 확보 방식. 배경 지식: sign-off/tapeout 프라이머
  [`issues/010-appendix-a`](issues/010-appendix-a-signoff-tapeout-primer.md).
- 가설 정식화 도구: `.claude/skills/meta-research/` (vendored, 검증 이력
  [`issues/013`](issues/013-hypothesis-skill-selection.md)) — `/meta-research`로 호출.

## 이전 사이클 참조 (main에 없음)

| 자산 | 위치 |
|---|---|
| 피벗 직전 전체 스냅샷 (사례 연구 1 코드·spec·wiki·experiments 리포트) | git tag `archive/pre-vibe-pivot-2026-08-23` |
| 3-layer 시절 자산 | branch `archive/integrated-program-3layer` |
| 이전 INTENT (3회 피벗 Learnings 이력) | `docs/INTENT-archive-2026-08-22.md` |
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
