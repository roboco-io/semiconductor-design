---
title: graphify 도입 설계 — Phase 1a Wiki 엔진 전면 대체
status: draft
decision-date: 2026-04-22
authors: [serithemage, claude-opus-4-7]
supersedes-scope:
  - src/semi_design_wiki/ (전체 모듈)
  - pyproject.toml의 wiki-init/wiki-sync/wiki-lint CLI entry points
  - .claude/skills/semi-design-wiki/
revises-in-place:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md §3.2 (L2 interfaces), §5 (G-score/Promotion), §7 (운영 규칙) — S2에서 v2로 재작성
related:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # 상위 program spec
  - https://github.com/safishamsi/graphify  # 도입 대상 도구
---

# graphify 도입 설계 — Phase 1a Wiki 엔진 전면 대체

## 0. 요약

Phase 1a에서 구축한 `src/semi_design_wiki/` 기반 LLM Wiki 엔진(frontmatter 계약·`wiki-lint`·`promotion_policy`)을 **graphify v0.4.25**로 전면 대체한다. graphify는 tree-sitter AST + Claude 서브에이전트 기반 의미 추출 + Leiden 커뮤니티 탐지를 결합한 지식 그래프 생성 도구로, MIT 라이선스·매우 활발한 업스트림·MCP 서버 제공을 특징으로 한다.

전환 전략은 **Strangler swap**(4단계) — (S1) graphify 실측 평가 → (S2) overview spec §3.2·§5·§7 개정 + Codex 3-round 재승인 → (S3) 구 코드·CLI 제거 + graph integrity check 신규 구현 → (S4) CLAUDE.md·`.claude/skills/`·wiki 레거시 정리. 각 단계에 롤백 게이트가 있다.

본 결정은 "`wiki/` 쓰기 계약 전면 폐기, graphify 표준(EXTRACTED/INFERRED/AMBIGUOUS 3-tier)에 의존"이라는 사용자 판단을 기반으로 한다.

## 1. 배경

### 1.1 현재 상태 (2026-04-22)

- `wiki/` — Phase 1a 엔진 완료. 약 93% 테스트 커버리지. 5 Python 모듈, 3 CLI, frontmatter 불변식과 `[[wikilink]]` 정합성 보장.
- 콘텐츠: K1 52 sources(α/β/γ/δ 축 4 파일), Phase 0 Q&A 세션 4 파일(a1~a4), 운영 규칙 3 파일(program·scoring·promotion_policy).
- 상위 계획: overview spec §3.2에서 `L2.memory.recall()`·`L2.skill_library.query()`·`L2.lint.check()` 인터페이스를 정의하고 있으며, `L2.lint.check()`만이 현재 구동 중인 L2 인터페이스다.

### 1.2 도입 동기

사용자 결정사항(2026-04-22 대화):
1. **도입 범위**: 전면 대체 (Phase 1a wiki 엔진 폐기).
2. **계약 처리**: frontmatter invariants·`promotion_policy`·`scoring` 모두 폐기, graphify 표준에 의존.
3. **`L2.lint.check()` 재정의**: (b) graph integrity check — orphan 노드 0, dangling edge 0, AMBIGUOUS 비율 임계선.
4. **실행 전략**: B — Strangler swap (4단계 roll forward).

### 1.3 graphify 개요

- 저장소: https://github.com/safishamsi/graphify · MIT · v0.4.25 (2026-04) · 32k ★ · 매우 활발.
- 스택: Python 3.10+, NetworkX + graspologic(Leiden) + tree-sitter + vis.js, Claude/GPT-4 기반 의미 추출, faster-whisper(비디오).
- 출력: `graphify-out/{graph.html, GRAPH_REPORT.md, graph.json, cache/}`.
- **실행 모드 (2026-04-22 검증)**:
  - Bash CLI는 서브커맨드만 허용: `graphify update <path>` (AST-only 증분, LLM 비용 0), `graphify query "..."`, `graphify path "A" "B"`, `graphify explain "X"`, `graphify install --platform ...` 등.
  - **전체 파이프라인(AST + Claude subagent 의미 추출 + Leiden + HTML)은 bash CLI로 실행되지 않는다.** 대신 `/graphify <path>` **슬래시커맨드**로 Claude Code 등 AI 에이전트 세션 안에서 skill.md 레시피를 따라 실행됨 — 에이전트가 파일별 subagent를 dispatch해 의미 추출.
  - Python API는 부분 노출: `graphify.detect.detect(path)` · `graphify.extract.extract(paths)` (AST) · `graphify.build.build(extractions)` · `graphify.cluster/analyze/export`. 하지만 **마크다운 Part B 의미 추출은 Python API 미노출** — agent-in-loop 필수.
- MCP 서버: `uv run python -m graphify.serve graph.json` — L2.memory.recall() 구현 후보 (graph.json 선행 필요).
- `--wiki` 플래그: `/graphify <path> --wiki` (슬래시커맨드 인자) 로 Leiden 커뮤니티별 마크다운 아티클 자동 생성.
- 3-tier 신뢰도: EXTRACTED(1.0) / INFERRED(<1.0) / AMBIGUOUS(검토 대기).

## 2. 비목표 (Out of scope)

- **L3 Content (Open-Ideation DSE)** 변경 — 본 설계는 L2 Substrate 범위에 한정.
- **`docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.3 canonical decision table의 publish/reframed/kill 기준 변경** — "최소 수정" 원칙. 증거 경로만 "wiki findings" → "graphify god-node + human-reviewed claim"으로 교체.
- **전역 `/Users/dohyunjung/Workspace/CLAUDE.md`의 "LLM Wiki 활용 규칙" 수정** — 다른 워크스페이스 프로젝트에 여전히 유효. 본 프로젝트 `CLAUDE.md`에 예외 조항만 추가.
- **H1·H2·H3 가설 자체의 수정** — 이는 overview spec §4의 영역.

## 3. 아키텍처 재정의

### 3.1 전환 전후 L2 Substrate 비교

| 영역 | 기존 (Phase 1a) | graphify 기반 |
|------|------------------|---------------|
| 쓰기 substrate | `wiki/` 마크다운 + frontmatter 계약 | **없음** — graphify는 읽기/탐색 지향. 원시 텍스트는 `wiki/raw/`에 그대로 유지. |
| 인덱스 | `wiki/index.md` (wiki-sync 생성) | `build/graph/GRAPH_REPORT.md` (graphify 생성) |
| 신뢰도 | frontmatter `confidence_score` | graphify 3-tier (EXTRACTED/INFERRED/AMBIGUOUS) |
| 승격 | `promotion_policy.md` 기반 수동 승격 | graphify UI에서 AMBIGUOUS → INFERRED/EXTRACTED 이동 |
| lint | `wiki-lint` (frontmatter + wikilink) | `make graph-lint` (graph integrity: orphan 0, dangling 0, AMBIGUOUS≤θ) |
| 탐색 | 수동 grep + wiki-link 추적 | `graphify query "..."` + `graph.html` |

### 3.2 L2 인터페이스 계약 (overview spec §3.2 개정 대상)

| Interface | graphify 기반 정의 |
|-----------|---------------------|
| `L2.memory.recall(query: str) → Node[]` | `graphify query`의 JSON 출력 또는 MCP 서버 응답. `tier` 필드 포함. |
| `L2.skill_library.query(name: str) → Skill` | graphify가 `.claude/skills/`도 인덱싱. 스킬 노드 direct lookup. |
| `L2.lint.check() → Report` | `scripts/graph_integrity_check.py` — orphan 노드=0, dangling edge=0, AMBIGUOUS 노드 수 ÷ 전체 노드 수 ≤ θ(초기값 0.3) |

### 3.3 의미 gap 명시

graphify의 confidence tier는 **추출 신뢰도**이지 **주장 타당성**이 아니다. Phase 1a의 `confidence_score`는 양자 모두를 암묵적으로 포함했다.

**완화책**: S2 spec 개정 시, `L2.memory.recall()` 소비자(L1/L3 agent)는 graphify tier를 "검토 필요도" 신호로만 해석하고, **주장 타당성은 H1/H3 실험 결과**에서만 판정한다. 이 원칙을 overview spec §5에 명시.

## 4. 4단계 Strangler 로드맵

### 4.1 S1 — Evaluate (graphify 실측 평가)

**목적**: graphify가 본 레포의 콘텐츠에 유효한지 empirical 증거 확보.

**입력 코퍼스** (3 trench)
- Narrative: `wiki/raw/papers/k1-{α,β,γ,δ}-*.md` 4개 + `wiki/raw/sessions/phase-0-a{1..4}-*.md` 4개
- Contract: `wiki/program/{program,scoring,promotion_policy}.md` 3개
- Code: `src/semi_design_wiki/*.py` 5 파일 + `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` excerpt

**실행 (2026-04-22 수정: CLI 실제 동작 반영)**

S1 스캔은 **이 Claude Code 세션 안에서 `/graphify .` 슬래시커맨드 equivalent workflow**를 1회 수행. 4-corpus 분리 스캔은 폐기 — 지표 M1~M5는 단일 graph.json에서 모두 평가 가능.

설치는 Task 1에서 완료(`uv tool install git+https://github.com/safishamsi/graphify`, PyPI name `graphifyy`, CLI `graphify`, version 0.4.25, commit 215b5d4).

스캔 레시피 (skill.md 준수):
1. `graphify.detect.detect(Path('.'))` — 파일 타입 분류
2. (Part A) `graphify.extract.extract(code_paths)` — AST, deterministic, LLM 비용 0
3. (Part B) 문서·마크다운 파일마다 Claude subagent dispatch — skill.md Step 3B의 dispatch 프롬프트 사용
4. `graphify.build.build(all_extractions)` → `nx.Graph`
5. `cluster` + `analyze.god_nodes` + `analyze.surprising_connections`
6. `export.generate_html` + `to_canvas`/JSON + GRAPH_REPORT.md → `graphify-out/`

출력 위치는 graphify 기본값 `graphify-out/`를 유지(이미 `.gitignore`에 포함). 평가 측정값만 `docs/superpowers/specs/2026-04-22-graphify-evaluation.md`에 커밋.

**합격 기준 (4/5 충족 시 S2 진행)**

| # | 지표 | 합격선 |
|---|------|-------|
| M1 | 코드 그래프 정밀도 | `src/semi_design_wiki/` 5 모듈과 주요 함수(`sync_index.regenerate`, `lint_wiki.check`, `frontmatter.parse_file`)가 노드로 정확히 추출 |
| M2 | K1 개념 커버리지 | 사전 정의된 **K1 핵심 개념 20개** 중 ≥16개가 노드로 존재 (개념 목록은 S1 착수 시 사용자가 별도 결정) |
| M3 | 교차 링크 | 한국어 paper ↔ session ↔ spec 세 trench에 걸친 inter-trench edge 수 ≥ 해당 세 trench의 합산 node 수 × 0.5 |
| M4 | 커뮤니티 정합성 | Leiden 커뮤니티 ≥ 1개가 K1 α/β/γ/δ 축 중 하나와 육안으로 매칭 |
| M5 | 비용·시간 | 전체 스캔 API 비용 < $5, 실행 시간 < 10분 |

**산출물**
- `docs/superpowers/specs/2026-04-22-graphify-evaluation.md` — 설치·실행 로그·지표·god-node 정성 리뷰·Pass/Fail 판정·S2 권고.
- `tmp/graphify-eval/` — graphify raw 출력 (gitignored).

**FAIL 분기**
- M1~M3 중 둘 이상 미달 → graphify 채택 철회, 사용자에게 **도입 포기 vs 접근안 C(spec-first) 재검토** 재질의.
- M5만 미달 → 비용 최적화 후 S1 재시도.

### 4.2 S2 — Spec revise (overview spec 개정)

**개정 대상 (in-place, v2 revision note 추가)**

- **§3.2 L2 Interface contracts** — 위 §3.2 표 반영.
- **§5 G-score / Promotion** — graphify 3-tier 기반 재작성. "Promotion = AMBIGUOUS → INFERRED/EXTRACTED 이동 via human review". 의미 gap(§3.3) 명시.
- **§5.3 Canonical Decision Table** — 최소 수정. 증거 경로만 교체.
- **§7 Operating rules** — `wiki/program/*.md` 내용을 spec §7에 흡수하거나 별도 참조 문서(`docs/superpowers/program/program.md`)로 이관.

**Codex 3-round review**
- 1차: 구조/일관성 (L2 인터페이스 호환성)
- 2차: 의미 gap 설명 충분성 (graphify confidence ≠ 주장 타당성)
- 3차: §5.3 증거 경로 변경이 H1/H3 falsifier를 훼손하지 않는지

**산출물**
- `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` v2 (헤더에 `revision: v2 (graphify 전환 반영, 2026-04-22)` 명시)
- `docs/superpowers/specs/2026-04-22-graphify-adoption-codex-review.md` — Codex 리뷰 로그

**게이트**: Codex 리뷰 3회 연속 fail 시 S3 진입 금지.

### 4.3 S3 — Code swap

**제거**
- `src/semi_design_wiki/` 전체 (5 파일)
- `tests/` 중 `test_init_wiki.py`·`test_sync_index.py`·`test_lint_wiki.py`·`test_frontmatter.py` + 관련 fixtures
- `pyproject.toml` `[project.scripts]` — `wiki-init` · `wiki-sync` · `wiki-lint`
- `Makefile`에서 wiki CLI 호출 타겟/예시

**추가**
- `pyproject.toml`에 `graphify>=0.4.25` 의존성 (dev group 권장). `uv.lock` 고정.
- `Makefile` 신규 타겟:
  - `make graph-update` → `graphify update .` (AST-only 증분, LLM 비용 0, 코드 수정 후 실행)
  - `make graph-build` → echo-only 안내 ("전체 빌드는 Claude Code 세션에서 `/graphify .` 실행. 대체 경로: S1 Task 3와 동일한 skill.md 레시피 수동 실행.")
  - `make graph-serve` → `uv run python -m graphify.serve graphify-out/graph.json` (MCP)
  - `make graph-lint` → `uv run python scripts/graph_integrity_check.py graphify-out/graph.json`
- `scripts/graph_integrity_check.py` — orphan 0, dangling 0, AMBIGUOUS 비율 ≤ θ=0.3 검증. 실패 시 non-zero exit.
- `tests/test_graph_integrity.py` — `graph_integrity_check.py`에 대한 pytest TDD 테스트.
- `.gitignore` 추가: `build/graph/`, `tmp/graphify-eval/`, `graphify-out/`, `.graphify-cache/`.

**커밋 시리즈 (main 직커밋)**
1. `chore(deps): add graphify to pyproject`
2. `feat(graph): add scripts/graph_integrity_check.py (+tests)`
3. `feat(make): add graph/graph-serve/graph-lint targets`
4. `refactor: remove src/semi_design_wiki and tests`
5. `refactor: drop wiki-init/sync/lint CLI entry points`

**합격 게이트**
- `make test` 전체 통과 (wiki 제외)
- `make graph-lint` 현재 레포 스캔 통과
- `make lint` (ruff) 통과
- 실패 시 `git revert` 로 커밋 4를 되돌려 Phase 1a 엔진 복구 가능

### 4.4 S4 — Doc & Skill cleanup

**프로젝트 `CLAUDE.md`**
- "Implementation Status" 표: Phase 1a 행을 "Wiki Engine → graphify 전환 (S1~S4)"로 교체
- "Commands" 섹션: `wiki-init/sync/lint` 제거, `make graph*` 추가
- "Repository Map": `wiki/`·`semi-design-wiki` 스킬·`semi_design_wiki` 모듈 참조 갱신
- "Before Non-Trivial Work" 1번의 `wiki/raw/sessions/` 참조 → `build/graph/` 또는 `graphify query`
- "Code Conventions"의 "Frontmatter" 규칙 삭제
- 상단 또는 "Project Context" 근처에 **전역 LLM Wiki 규칙 예외 조항** 추가: "본 프로젝트는 `wiki/` 대신 graphify `build/graph/graph.json` 사용"

**전역 `/Users/dohyunjung/Workspace/CLAUDE.md`**
- **변경 없음** (다른 워크스페이스 프로젝트에 여전히 유효)

**`.claude/skills/`**
- `semi-design-wiki/` — 폐기 (디렉터리 삭제, plugin manifest / `.claude/settings.json`에서 엔트리 제거)
- `semi-design-learning/` — 부분 개정. Phase 0 Q&A 세션은 `wiki/raw/sessions/phase-0-*.md`에 계속 저장(graphify 입력으로 살아남음). "wiki ingest 예정" 언급만 "graphify 자동 인덱싱"으로 교체. 트리거("학습 재개", "마인드맵")·주요 UX는 유지.
- `handoff/` — 변경 없음

**레거시 문서**
- `docs/eda_agent_handoff.md` — 변경 없음 (이미 Superseded 명시됨)
- `docs/superpowers/plans/` — 변경 없음 (historical)

**콘텐츠 보존**
- `wiki/raw/**` — **전부 유지**. graphify seed corpus로 재활용.
- `wiki/program/*.md` — S2에서 spec §7로 내용 흡수 후 **파일 삭제**
- `wiki/index.md` — 삭제 (GRAPH_REPORT.md가 대체)

**auto memory 정리** (`/Users/dohyunjung/.claude/projects/.../memory/`)
- `project_core_intent.md`에 "Karpathy Wiki 패턴" 언급 있으면 "graphify 기반 그래프 지식 인덱스"로 갱신

**S4 커밋 시리즈**
1. `docs(claude-md): update project CLAUDE.md for graphify`
2. `chore(skills): remove semi-design-wiki skill`
3. `chore(skills): retarget semi-design-learning to graphify`
4. `docs(wiki): absorb wiki/program/* into spec and remove`
5. `docs(wiki): remove wiki/index.md (replaced by GRAPH_REPORT.md)`

## 5. 테스트 전략

- **S1 평가 테스트**: 수동 — 평가 리포트로 대체 (자동화 없음).
- **S3 graph integrity check 테스트**: `tests/test_graph_integrity.py` TDD — fixture로 작은 `graph.json` 만들어 (a) clean graph 통과, (b) orphan 노드 주입 시 실패, (c) AMBIGUOUS 비율 0.5 주입 시 실패, (d) dangling edge 주입 시 실패 케이스 검증.
- **회귀**: S3 이후 `make test` 전체가 통과하고, 커버리지 ≥85% (Phase 1a 삭제로 대상 모듈 축소).

## 6. 성공 기준 (전체 도입)

- [ ] S1 평가 리포트의 M1~M5 중 ≥4개 합격
- [ ] overview spec v2가 Codex 3-round 통과
- [ ] `src/semi_design_wiki/` 제거 후 `make test`·`make graph-lint`·`make lint` 모두 통과
- [ ] 프로젝트 CLAUDE.md·`.claude/skills/` 정리 완료, `semi-design-learning` 스킬 트리거가 graphify-aware로 동작 확인

## 7. 롤백 계획

- **S1 FAIL** (M1~M3 중 2개 미달) → graphify 채택 철회. 작성된 평가 리포트는 "graphify 도입 보류" 근거로 남김.
- **S2 FAIL** (Codex 3회 연속 fail) → spec 개정 철회, S1 결과는 참고 자료로 보관, graphify 평가만 완료된 상태로 종료.
- **S3 FAIL** (`make test` 실패 지속) → `git revert` 로 삭제 커밋(#4) 되돌림. Phase 1a 엔진 복구.
- **S4 FAIL** (스킬 재구성 실패) → `.claude/skills/semi-design-wiki/` 복원 커밋 (git 히스토리에서), `semi-design-learning` 개정 되돌림.

## 8. 열린 결정사항

- **S1 착수 시** — M2의 "K1 핵심 개념 20개" 목록 확정 (사용자 결정, ex-post 합리화 방지).
- **S2 착수 시** — `wiki/program/*.md` 내용을 spec §7 인라인 vs `docs/superpowers/program/`로 이관 중 선택.
- **S3 착수 시** — graphify를 main dependency vs dev dependency 배치 선택 (CI에서 graphify 사용 여부에 따라).

위 결정은 해당 단계 착수 시점에 별도 `AskUserQuestion`/`Learn by Doing` 요청으로 확인한다.
