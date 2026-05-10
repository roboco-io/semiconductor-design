# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This repo is an **AI agent research project**: **"Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator Design"** (통합 프로그램, 2026-04-19 overview spec). 3-layer 구조 — **L1 Process** (SHA-pinned Nix bundle + AWS Fargate Spot) + **L2 Substrate** (report-grounded memory + reversible-patch skill library) + **L3 Content** (Open-Ideation Gemmini DSE on MLPerf Tiny v1.3 streaming). Deliverables: 논문 + 오픈소스 reference + process reasoning-trace evidence. Target: **academic/process novelty vs commercial chips**, not absolute PPA.

All novelty hypotheses (H1/H2/H3 with falsifiers), evaluation thresholds, publish/reframed/kill decisions, and layer interfaces live in the overview spec. §5.3 **canonical decision table** is the single source of truth for publish/kill — no other file declares its own criteria.

The implemented code today is `src/semi_design_runner/` (L1 Process runner) + `scripts/graph_integrity_check.py` (L2.lint.check substrate). L1/L2/L3 agent system is designed but not yet built. Do not assume other subsystems exist in code.

> **컨텍스트 관리 정책 (2026-05-09 갱신, wiki-first 하이브리드)**: [Karpathy LLM Wiki 72-run 벤치마크](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/) (wiki vs graphify: 토큰 −53.6%, 시간 −39.3%, 품질 +6%, p<0.01)를 근거로 **`wiki/index.md` 기반 마크다운 위키를 default 컨텍스트 라우팅**으로 사용한다. 답변 작성 시 `[[wiki/페이지]]` 인용을 강제한다. graphify는 **보조 도구** — cross-component path 탐색(예: spec 결정 ↔ source paper 의존성)이나 wiki에 아직 컴파일되지 않은 영역에 한해 `make graph-serve` MCP / `uv run graphify query "..."`를 사용한다. 2026-04-22의 graphify-only 결정은 본 항목으로 대체된다 (graphify-out/는 보조용으로 commit 유지).
>
> **범위 (layer 분리)**: 본 정책은 **human/LLM이 답변 작성 시 컨텍스트를 회수하는 라우팅 layer**만 다룬다. agent system 내부 API인 `L2.memory.recall` / `L2.skill_library.query` / `L2.lint.check` (overview spec §3.2 + L2-substrate-design §5.1)는 **graphify를 backend로 spec-freeze** 상태 — 본 wiki-first 라우팅 결정과 독립이며, 변경은 L2 spec-owner의 Codex 3-round review를 거쳐야 한다.

## Intent

본 프로젝트의 *Why · What · Not · Learnings* 는 [`INTENT.md`](INTENT.md) 에 정리되어 있다 (status: clarified, 2026-05-10 작성). 메타 목적 두 가지 — (1) 의도공학(intent engineering) 패러다임 우수성의 사례 연구, (2) Operator 학습 ↔ 프로젝트 진화의 co-evolution. **본 CLAUDE.md 의 모든 컨벤션 · 작업 규칙은 `INTENT.md` 의 Not 섹션을 어긴 의사결정을 차단하기 위한 substrate로 작동**한다. 새 spec/결정·위임 task 정의 시 `INTENT.md` 와 정합하는지 먼저 점검한다. 학습이 누적되면 `INTENT.md` Learnings 섹션에 기록 → 의도가 진화하고, 진화한 의도가 다시 spec·wiki·결정을 변형시키는 co-evolution 사이클이 본 프로젝트의 publishing 축.

## Implementation Status

현재는 통합 프로그램 **G0 bootstrap → G1** 전환 단계. 이전 1a~6 번호는 구 spec(archived) 기준이라 새 G0~G4 gate로 매핑됨.

| Gate / Sub-plan | Scope | Status |
|---|---|---|
| Phase 1a — Wiki Skill Engine | `src/semi_design_wiki/`, `tests/` | ⛔ **엔진 코드 폐기** (2026-04-22 graphify 전환, `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md`). 마크다운 위키 자체는 2026-05-09 L23 행에서 운영 부활. |
| Wiki → graphify 전환 (2026-04-22 history) | `scripts/graph_integrity_check.py` + `graphify-out/graph.json` + graphifyy v0.4.25 git dep | ✅ S1~S4 완료. 2026-05-09 wiki-first hybrid로 superseded — graphify는 보조 path 쿼리로 잔존. |
| Wiki-first 컨텍스트 라우팅 (2026-05-09) | `wiki/index.md` + 컴파일 페이지 (Karpathy 패턴, default 라우팅) — graphify는 보조 path 쿼리로 격하 | ✅ Phase-0 sessions 5 + K1 evidence 4 + K2 evidence 4 + C-EDA flow 1 + F-PDK formats 1 (총 **15 페이지** = concept 6 + policy 1 + synthesis 8) 완료. K1+K2 evidence 그래프 종결 (8 페이지). 다음 ingest 후보: B branch (HDL) · KG-E DDB · Si2 Liberty / Cadence LEF·DEF / OpenSTA full ref. |
| G0 Program bootstrap | K1 52 + K2 61 sources + direction report + overview spec + §7 operating rules + issues 재배치 | ✅ complete |
| G1 L1 Process | SHA-pinned Nix (LibreLane 3.0.2 + OpenROAD + Yosys + sky130A) + Fargate Spot (ephemeral 200 GiB) + SFN Standard workflow + `make run` gcd; kill gates KG-A~KG-E | pending — L1 파생 spec (K2 ζ 갱신 필요) |
| G2 L2 Substrate | typed-frontmatter memory + QMD + findings/failures/decisions + `L2.lint`·`skill_library`·`memory` interfaces | pending — L2 파생 spec (L1 완료 후 병렬) |
| G3 L3 Content | Open-Ideation DSE on Gemmini + MLPerf Tiny v1.3 streaming, gcd/ibex/aes | pending — L3 파생 spec, License Gate §13 선행 |
| G4 통합 실험 | 복리 효과 + reasoning trace + ORFS-agent 대조. publish/reframed/kill 은 overview spec §5.3 | pending |

Phase 0 (learning) runs **in parallel** with implementation; its state lives in `docs/learning/phase-0-curriculum.md`, `wiki/raw/sessions/phase-0-*.md` (불변 원본), and the compiled `wiki/phase-0-eda-operator-lens.md` policy page (Branch A 진입점, 2026-05-09 컴파일).

## Commands

```bash
make install                     # uv sync --all-extras
make test                        # pytest -v
make lint                        # ruff check src tests scripts
make fmt                         # ruff format src tests scripts
make clean                       # drop caches/build artifacts

make graph-update                # graphify update . (AST-only incremental, fast)
make graph-build                 # (안내만) full rebuild은 /graphify . 로 AI 세션에서
make graph-serve                 # graphify MCP server (L2.memory.recall 공급)
make graph-lint                  # graph integrity check (L2.lint.check: orphan=0 / dangling=0 / AMBIGUOUS≤0.3)
uv run graphify query "..."      # ad-hoc BFS 질의
uv run graphify explain "<node>" # 단일 노드 plain-language 설명

# single test
uv run pytest tests/test_graph_integrity.py::test_clean_graph_passes -v
```

Python 3.12, `uv`-managed. Wheel target `src/semi_design_runner/` with CLI entry points (`semi-run`, `semi-metric-collector`) declared in `pyproject.toml`. Dev dep에 `graphifyy` (graphify git+SHA, PyPI dist 이름은 double-y, CLI는 `graphify`).

## Architecture (big picture)

Two overlapping views (둘 다 overview spec `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`에서 정의됨 — 본 CLAUDE.md는 요약이고 spec이 authoritative):

- **4-plane** — Local / AWS / Tool / Knowledge (실행 substrate)
- **3-layer** — L1 Process / L2 Substrate / L3 Content (연구 프로그램 구성). Layer 간 인터페이스는 spec §3.2 contract table에 고정 — `L1.run(spec_uri)`, `L2.skill_library.query()`, `L2.memory.recall()`, `L2.lint.check()`. Breaking change 시 overview spec 재승인 필요.

Planes:
- **Local plane**: Python CLI orchestrator + LLMs (Claude Code SDK + Codex SDK). All LLM calls run locally.
- **AWS plane** (CDK TypeScript, not yet written): Step Functions `Map` (maxConcurrency=10) → Fargate Spot per-candidate pipeline. S3 artifact lake + DynamoDB 4 tables + ECR. SHA-pinned via `lockfile.yaml` (spec §6.2).
- **Tool plane**: Wrapped open-source EDA binaries (Yosys, **LibreLane 3.0.2** — OpenLane2 → LibreLane rename은 K1에서, 2.4 → 3.0.2 버전 갱신은 K2 ζ 2026-04-22에서 확정, OpenROAD, Verilator, cocotb, mlcommons/tiny **v1.3**). **Anti-reinvention principle**. Efabless 경로는 **2025-02 셧다운으로 폐기** — 대체 경로는 Iter 3+ 결정.
- **Knowledge plane**: `wiki/index.md` + 컴파일 페이지 (default 라우팅, Karpathy LLM Wiki 패턴) + `wiki/raw/**` (불변 seed corpus — K1+K2 papers, sessions, blogs, repos) + `graphify-out/{graph.json, GRAPH_REPORT.md, graph.html}` (보조 path 쿼리, Option A+ commit policy) + `scripts/graph_integrity_check.py` (L2.lint.check).

**Search strategy** is **2-tier**:
1. Template DSE over Gemmini parameters (safe baseline)
2. Open Ideation — agents propose **template-breaking microarchitectures** (H1b novelty dimension)

Never reduce the project to a pure parameter sweep — ORFS-agent(2025) 이미 그 영역 공략함. **H1b "non-knob structural patch"** (spec 부록 C exclusion list 대상 아닌 transform)가 idea-generation dimension의 핵심 지표.

**Evaluation/decision rule**: publish/reframed-publish/kill 분기는 overview spec **§5.3 Canonical Decision Table**만이 결정 — `H1 pass count × H3 validity` (H2는 보조). 본 리포의 어떤 문서도 자체 publish/kill 기준을 선언하지 않는다.

## Code Conventions

- **Direct commits to `main`** is the user's explicit workflow (no feature branches for now).
- **Conventional commit prefixes** in active use: `docs(phase-0): ...`, `docs(wiki): ...`, `docs: ...`, `chore: ...`, `test: ...`. Keep subject imperative.
- **Tests**: pytest; use `tmp_path` and fixtures. Never touch real `wiki/raw/` in tests — write fixture graphs to `tmp_path`. `scripts/graph_integrity_check.py` supports both NetworkX (`links`) and graphify-native (`edges`) JSON formats.
- **Coverage target**: ≥85% per module for `src/semi_design_runner/`. `scripts/` 라인 수가 적어 coverage target은 not enforced이지만 새 path마다 test 필수.
- **Ruff 100 char line limit**, `target-version = "py312"`. `src tests scripts` 세 디렉토리 모두 lint/fmt 대상.

## Repository Map (non-obvious parts)

- `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` — **THE** active program overview spec. Codex 3-round review 통과. Read before any non-trivial change to program-level decisions.
- `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` — **ARCHIVED** 2026-04-19. Retained for history only. Do NOT base new work on it (Efabless 셧다운·OpenLane2 rename·MLPerf v1.2 등 stale gates 다수).
- `docs/knowledge-base/2026-04-19-k1-direction-report.md` — K1 지식 기반 방향 판단 리포트. 통합 프로그램 방향의 근거.
- `docs/superpowers/plans/` — per-phase TDD implementation plans. Phase 1a done; L1/L2/L3 파생 plans pending.
- `docs/learning/phase-0-curriculum.md` — **retargeted 2026-04-19** to "EDA operator lens". Source of truth for learning.
- `docs/eda_agent_handoff.md` — prior ORFS autotuning-focused 핸드오프. **Superseded** by integrated program — ORFS-agent(2025) 존재로 autotuning 단독 MVP 가정은 무효.
- `issues/*.md` — local issue tracker. 2026-04-19 재배치 — 각 이슈 상단 "재배치 노트" 참조.
- `wiki/{slug}.md` — **컴파일된 default 컨텍스트 페이지** (concept · policy · synthesis · decision · entity types). frontmatter `sources` / `related_specs` 명시 필수, 답변 시 `[[slug]]` 인용. 2026-05-09 1차 ingest 9 페이지 (Phase-0 4 concept + 1 policy + K1 4 synthesis), K2 4 papers pending.
- `wiki/raw/sessions/phase-0-*.md` — Phase 0 Q&A 불변 원본. wiki ingest로 `wiki/{concept}.md` 컴파일 페이지 생성, graphify는 보조로 인덱싱.
- `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md` — K1 축별 52 sources (방향판단).
- `wiki/raw/papers/k2-{epsilon,zeta,eta,theta}-*.md` — K2 축별 61 sources (S3/G1/L2 파생 spec 착수 전 결정 baseline, 2026-04-22).
- `wiki/raw/imports_manifest.yaml` — K1+K2 structured index with decision anchors, spec_contradictions, critical_read highlights.
- `scripts/graph_integrity_check.py` — L2.lint.check substrate (orphan=0 / dangling=0 / AMBIGUOUS≤0.3).
- `graphify-out/{graph.json, GRAPH_REPORT.md, graph.html}` — **보조** path-query 도구 (커밋 대상, Option A+ policy). cross-component 의존성 탐색에만 사용 — default 컨텍스트 라우팅은 `wiki/index.md`. `graphify-out/cache/` 및 `.graphify_*` 는 gitignore.
- `graphify-out/memory/` — `graphify query` / `path` / `explain` 결과가 markdown으로 저장되어 다음 `--update` 시 재인제스트.
- `.claude/skills/semi-design-learning/` — Phase 0 학습 skill (wiki-aware, 학습 세션 후 `wiki/raw/sessions/`에 저장 → wiki ingest로 `wiki/{concept}.md` 컴파일 → 보조로 `make graph-update`). Triggers on "학습 재개", "Phase 0", "마인드맵".

## Project-Specific Working Rules

- **Learning lens** (feedback, 2026-04-19): Phase 0 is for the user to become an **EDA operator who can supervise/debug agents**, not a chip designer. When writing learning material, prioritize reading LLM-generated RTL critically, interpreting `*.rpt` files (synth area, STA slack, DRC violations), and understanding file formats (`.v/.lib/.lef/.def/.sdc`). Skip deep theory unless it blocks report interpretation. `C` (EDA Flow) and `F` (PDK formats) are elevated; `B/D/E` are compact.
- **Assistant-led Q&A**: For Phase 0 sessions, I explain 5–10 lines first, user confirms or asks. Record Q&A into the session file as it happens. Mark complete only after the user says "다음" or equivalent.
- **Open decisions stay in `issues/`**: Don't inline them into the spec. When a design fork appears, create an issue file using `issues/README.md` conventions.
- **Korean content is expected** throughout docs, commits, and wiki body. Technical terms (file formats, tool names, module identifiers) stay in English. **예외**: wiki page slug과 frontmatter `title`은 영어/하이픈 (Obsidian `[[link]]` 호환 + cross-tool grep 안정성). 본문·표·`sources`·`related_specs` 값은 Korean.
- **wiki ingest 워크플로**: 새 raw 노트는 `wiki/raw/{sessions,papers,blogs,repos,docs,benchmarks}/`에 드롭 → `documentation:llm-wiki` skill의 ingest 5단계로 `wiki/{slug}.md` 컴파일 → frontmatter `sources`/`related_specs` 명시 → `wiki/log.md` 항목 추가 → 보조로 `make graph-update`. 컴파일 페이지 type은 `concept`/`decision`/`policy`/`synthesis`/`entity` 중 선택 (skill 문서 [page-templates.md] 참조).

## Before Non-Trivial Work

1. **위키 우선 조회** — `wiki/index.md`에서 관련 페이지 진입 후 `[[wiki-link]]` 2-hop 확장으로 컨텍스트 확보. 답변 작성 시 `[[페이지]]` 인용. Phase-0 학습 상태는 `docs/learning/phase-0-curriculum.md` 와 `wiki/raw/sessions/` 원본 참조.
2. **보조 그래프 쿼리** — wiki에 답이 부족하거나 cross-component 경로(spec ↔ source 의존성)가 필요하면 `uv run graphify query "..."` / `make graph-serve` MCP. Community·God Node 카탈로그는 `graphify-out/GRAPH_REPORT.md`.
3. Read the relevant plan in `docs/superpowers/plans/` for implementation phases, or the spec §3 / §9 for architecture questions.
4. Search `issues/` for any open decision that blocks the area you're about to touch.
5. For anything affecting RTL/EDA flow design — remember the project is **vibe-coding + AutoResearch**, not a parameter-sweep DSE.
