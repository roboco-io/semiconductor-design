# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This repo is an **AI agent research project**: **"Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator Design"** (통합 프로그램, 2026-04-19 overview spec). 3-layer 구조 — **L1 Process** (SHA-pinned Nix bundle + AWS Fargate Spot) + **L2 Substrate** (report-grounded memory + reversible-patch skill library) + **L3 Content** (Open-Ideation Gemmini DSE on MLPerf Tiny v1.3 streaming). Deliverables: 논문 + 오픈소스 reference + process reasoning-trace evidence. Target: **academic/process novelty vs commercial chips**, not absolute PPA.

All novelty hypotheses (H1/H2/H3 with falsifiers), evaluation thresholds, publish/reframed/kill decisions, and layer interfaces live in the overview spec. §5.3 **canonical decision table** is the single source of truth for publish/kill — no other file declares its own criteria.

The implemented code today (`src/semi_design_wiki/`) is only the **wiki/knowledge layer (Phase 1a)**. L1/L2/L3 agent system is designed but not yet built. Do not assume other subsystems exist in code.

## Implementation Status

현재는 통합 프로그램 **G0 bootstrap → G1** 전환 단계. 이전 1a~6 번호는 구 spec(archived) 기준이라 새 G0~G4 gate로 매핑됨.

| Gate / Sub-plan | Scope | Status |
|---|---|---|
| Phase 1a — Wiki Skill Engine | `src/semi_design_wiki/`, `tests/` | ✅ done |
| G0 Program bootstrap | K1 52 sources + direction report + overview spec + program/ rules + issues 재배치 | 🟡 near-complete |
| G1 L1 Process | SHA-pinned Nix (LibreLane 2.4 + OpenROAD + Yosys + sky130A) + Fargate Spot + SFN + `make run` gcd; kill gates KG-A~KG-E | pending — L1 파생 spec 필요 |
| G2 L2 Substrate | typed-frontmatter memory + QMD + findings/failures/decisions + `L2.lint`·`skill_library`·`memory` interfaces | pending — L2 파생 spec (L1 완료 후 병렬) |
| G3 L3 Content | Open-Ideation DSE on Gemmini + MLPerf Tiny v1.3 streaming, gcd/ibex/aes | pending — L3 파생 spec, License Gate §13 선행 |
| G4 통합 실험 | 복리 효과 + reasoning trace + ORFS-agent 대조. publish/reframed/kill 은 overview spec §5.3 | pending |

Phase 0 (learning) runs **in parallel** with implementation; its state lives in `docs/learning/phase-0-curriculum.md` and `wiki/raw/sessions/phase-0-*.md`.

## Commands

```bash
make install                     # uv sync --all-extras
make test                        # pytest -v
make lint                        # ruff check src tests
make fmt                         # ruff format src tests
make clean                       # drop caches/build artifacts

uv run wiki-init --root wiki     # idempotent wiki scaffold
uv run wiki-sync --root wiki     # regenerate wiki/index.md atomically
uv run wiki-lint --root wiki     # validate frontmatter + links

# single test
uv run pytest tests/test_lint_wiki.py::test_low_confidence_flagged -v
```

Python 3.12, `uv`-managed. Wheel target `src/semi_design_wiki/` with CLI entry points (`wiki-init`, `wiki-sync`, `wiki-lint`) declared in `pyproject.toml`.

## Architecture (big picture)

Two overlapping views (둘 다 overview spec `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`에서 정의됨 — 본 CLAUDE.md는 요약이고 spec이 authoritative):

- **4-plane** — Local / AWS / Tool / Knowledge (실행 substrate)
- **3-layer** — L1 Process / L2 Substrate / L3 Content (연구 프로그램 구성). Layer 간 인터페이스는 spec §3.2 contract table에 고정 — `L1.run(spec_uri)`, `L2.skill_library.query()`, `L2.memory.recall()`, `L2.lint.check()`. Breaking change 시 overview spec 재승인 필요.

Planes:
- **Local plane**: Python CLI orchestrator + LLMs (Claude Code SDK + Codex SDK). All LLM calls run locally.
- **AWS plane** (CDK TypeScript, not yet written): Step Functions `Map` (maxConcurrency=10) → Fargate Spot per-candidate pipeline. S3 artifact lake + DynamoDB 4 tables + ECR. SHA-pinned via `lockfile.yaml` (spec §6.2).
- **Tool plane**: Wrapped open-source EDA binaries (Yosys, **LibreLane 2.4** — 기존 OpenLane2 rename, OpenROAD, Verilator, cocotb, mlcommons/tiny **v1.3**). **Anti-reinvention principle**. Efabless 경로는 **2025-02 셧다운으로 폐기** — 대체 경로는 Iter 3+ 결정.
- **Knowledge plane**: `wiki/` (Phase 1a engine) + `wiki/findings/`·`failures/`·`decisions/` + `wiki/program/` (operating rules) + QMD index.

**Search strategy** is **2-tier**:
1. Template DSE over Gemmini parameters (safe baseline)
2. Open Ideation — agents propose **template-breaking microarchitectures** (H1b novelty dimension)

Never reduce the project to a pure parameter sweep — ORFS-agent(2025) 이미 그 영역 공략함. **H1b "non-knob structural patch"** (spec 부록 C exclusion list 대상 아닌 transform)가 idea-generation dimension의 핵심 지표.

**Evaluation/decision rule**: publish/reframed-publish/kill 분기는 overview spec **§5.3 Canonical Decision Table**만이 결정 — `H1 pass count × H3 validity` (H2는 보조). 본 리포의 어떤 문서도 자체 publish/kill 기준을 선언하지 않는다.

## Code Conventions

- **Direct commits to `main`** is the user's explicit workflow (no feature branches for now).
- **Conventional commit prefixes** in active use: `docs(phase-0): ...`, `docs(wiki): ...`, `docs: ...`, `chore: ...`, `test: ...`. Keep subject imperative.
- **Tests**: pytest; use `tmp_path` and fixtures from `tests/conftest.py`, never touch real `wiki/`. Integration tests cover both library-level and `click.testing.CliRunner` paths — maintain both when adding CLI commands.
- **Coverage target**: ≥85% per module. The Phase 1a suite sits at ~93%; don't regress when editing `src/semi_design_wiki/`.
- **Frontmatter**: every wiki page starts with `---\n...\n---\n`. `frontmatter.py:parse_file` expects `\n---\n` as the closing delimiter (not just `---`). Match this when writing pages by hand.
- **Ruff 100 char line limit**, `target-version = "py312"`.

## Repository Map (non-obvious parts)

- `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` — **THE** active program overview spec. Codex 3-round review 통과. Read before any non-trivial change to program-level decisions.
- `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` — **ARCHIVED** 2026-04-19. Retained for history only. Do NOT base new work on it (Efabless 셧다운·OpenLane2 rename·MLPerf v1.2 등 stale gates 다수).
- `docs/knowledge-base/2026-04-19-k1-direction-report.md` — K1 지식 기반 방향 판단 리포트. 통합 프로그램 방향의 근거.
- `docs/superpowers/plans/` — per-phase TDD implementation plans. Phase 1a done; L1/L2/L3 파생 plans pending.
- `docs/learning/phase-0-curriculum.md` — **retargeted 2026-04-19** to "EDA operator lens". Source of truth for learning.
- `docs/eda_agent_handoff.md` — prior ORFS autotuning-focused 핸드오프. **Superseded** by integrated program — ORFS-agent(2025) 존재로 autotuning 단독 MVP 가정은 무효.
- `issues/*.md` — local issue tracker. 2026-04-19 재배치 — 각 이슈 상단 "재배치 노트" 참조.
- `wiki/raw/sessions/phase-0-*.md` — Phase 0 Q&A originals. Ingest 예정 (Phase 1b).
- `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md` — K1 축별 52 sources. `wiki/raw/imports_manifest.yaml`이 structured index.
- `wiki/program/{program,scoring,promotion_policy}.md` — 운영 헌법 · 평가/승격 기준. Overview spec §7 · §5 구체화.
- `.claude/skills/semi-design-learning/` — Phase 0 학습 skill. Triggers on "학습 재개", "Phase 0", "마인드맵".
- `.claude/skills/semi-design-wiki/` — shell for wiki ingest. Content to be filled in Phase 1b.

## Project-Specific Working Rules

- **Learning lens** (feedback, 2026-04-19): Phase 0 is for the user to become an **EDA operator who can supervise/debug agents**, not a chip designer. When writing learning material, prioritize reading LLM-generated RTL critically, interpreting `*.rpt` files (synth area, STA slack, DRC violations), and understanding file formats (`.v/.lib/.lef/.def/.sdc`). Skip deep theory unless it blocks report interpretation. `C` (EDA Flow) and `F` (PDK formats) are elevated; `B/D/E` are compact.
- **Assistant-led Q&A**: For Phase 0 sessions, I explain 5–10 lines first, user confirms or asks. Record Q&A into the session file as it happens. Mark complete only after the user says "다음" or equivalent.
- **Open decisions stay in `issues/`**: Don't inline them into the spec. When a design fork appears, create an issue file using `issues/README.md` conventions.
- **Korean content is expected** throughout docs, commits, and wiki. Technical terms (file formats, tool names, module identifiers) stay in English.

## Before Non-Trivial Work

1. Check `docs/learning/phase-0-curriculum.md` and `wiki/raw/sessions/` for the latest learning state.
2. Read the relevant plan in `docs/superpowers/plans/` for implementation phases, or the spec §3 / §9 for architecture questions.
3. Search `issues/` for any open decision that blocks the area you're about to touch.
4. For anything affecting RTL/EDA flow design — remember the project is **vibe-coding + AutoResearch**, not a parameter-sweep DSE.
