# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context (2026-08-25 사이클 3)

**목표(Operator 고정)**: 반도체 설계에 **실제 유용한 소프트웨어/모델을 바이브 코딩으로 개발**한다. 산출물의 실용성이 목적, 바이브 코딩은 방법. 유용성은 객관 지표(외부 벤치마크 > 채택 증거 > 시간 절감 표)로 검증.

**4트랙 병렬** (Operator 승인, [`issues/001`](issues/001-build-target-selection-brief.md)):

| 트랙 | 산출물 | 가설 | 계획서 |
|---|---|---|---|
| A | RTL-to-GDS 실험 추적 도구 → QoR 조기 예측기 | H1/H1.1 **refuted** | [`tracks/A-run-tracker/`](tracks/A-run-tracker/) |
| B | STA 리포트 분석기 | H2 (대기) | [`tracks/B-sta-analyzer/`](tracks/B-sta-analyzer/) |
| C | 플로우 실패 진단기 | H3 **refuted** | [`tracks/C-flow-doctor/`](tracks/C-flow-doctor/) |
| D | IR drop 경량 예측 모델 | H5 (진행) | [`tracks/D-irdrop/`](tracks/D-irdrop/) |

- 상태의 원천: [`research-tree.yaml`](research-tree.yaml) + [`research-log.md`](research-log.md). 조사 근거: [`literature/survey.md`](literature/survey.md).
- **트랙 폴더 통합(2026-08-26)**: 각 트랙의 계획·protocol·결과·튜토리얼은 `tracks/<트랙>/`에 한곳에. 총괄: [`tracks/README.md`](tracks/README.md). 구 `plans/`·`experiments/`는 폐지.
- **튜토리얼 규율(2026-08-26)**: 판정·주요 마일스톤 커밋 시 해당 `tracks/<트랙>/tutorial.md`의 "실험 일지"를 같은 작업 흐름에서 갱신(12살 눈높이 서술형 + 주관식 퀴즈, 모범답안은 `<details>`). 커밋 prefix `docs(tutorial):` — results 커밋과 분리. 상세 규칙: tracks/README.md.
- **트랙 착수 규율**: 구현 시작 전 해당 트랙의 유용성 판정 기준을 protocol로 LOCK(Codex 게이트 심사) 후 이 리포에 커밋. plan 커밋과 results 커밋 절대 병합 금지.
- 트랙 구현은 독립 public repo(Apache-2.0), 이 리포는 연구 관리(계획·프로토콜·결과·로그) 전용.
- 가설 정식화 도구: `.claude/skills/meta-research/` — `/meta-research`.

## 이전 사이클 참조 (main에 없음 — 근거로 사용 금지)

| 자산 | 위치 |
|---|---|
| 사이클 2 (EDA 하네스 연구, H1 protocol LOCKED) | tag `archive/eda-harness-cycle-2026-08-25` |
| 사이클 1 (바이브 코딩 INTENT·H1.1 스모크) | tag `archive/pre-eda-zerobase-pivot-2026-08-25` |
| EDA surrogate 사례 연구 스냅샷 | tag `archive/pre-vibe-pivot-2026-08-23` |
| git 미추적 실험 아티팩트 1.9GB | `~/Backups/semiconductor-design-experiments-2026-08-23.tar.gz` |

## Code Conventions

- **Direct commits to `main`** (Operator 워크플로우). Conventional commit prefix (`docs:` `chore:` `feat:` `research(plan/code/results):`), subject는 명령형.
- 설계 fork·열린 결정은 인라인하지 말고 `issues/`에 파일로.

## Operating Invariants (검증된 메타 패턴 — 유지)

- **웹 조사는 exa MCP만** (`web_search_exa`/`web_fetch_exa`). Perplexity 금지. 응답 수신 직후 first check = citation 개수, 0이면 전체 기각 후 재조회.
- **추측 vs grep 검증**: 정합 작업 전 반드시 grep으로 사실 확인. 추측을 기록물에 남기지 않는다.
- **사전 고정 판정**: 판정 기준은 결과 확인 전 LOCK, 사후 변경 금지(이탈은 EXPLORATORY 라벨). git 커밋 순서가 사전등록 증명.
- **생성 엔진 ≠ 심사 엔진**: 설계·판정·릴리스 게이트 리뷰는 Codex (`.claude/skills/codex-review-approval/`).
- **바이브 코딩 품질 게이트**: 라인 리뷰 대신 기계적 게이트 — 자동 테스트+CI(커버리지 게이트), golden 대조, 외부 벤치마크 (Normal Computing·CoreSmith 패턴).
- **구독 CLI만**(metered LLM API 금지) · **로컬·무료 컴퓨트만** · **맹목적 자율 금지**(객관적 게이트 없이 자율 머지 금지).
- **Agent definition staleness**: `.claude/agents|skills|settings`·`.mcp.json` 변경은 같은 세션에서 활성화되지 않음 — 세션 재시작 후 재호출.
