# semiconductor-design

AI-agent research for open-source EDA + DL accelerator design — **Report-Grounded Vibe-Coded AutoResearch** (통합 프로그램, 2026-04-19).

## Program overview

See [통합 프로그램 overview spec](docs/superpowers/specs/2026-04-19-integrated-research-program-design.md) for the authoritative design. 3-layer 구조 — **L1 Process** (SHA-pinned Nix + AWS Fargate Spot) + **L2 Substrate** (report-grounded memory + reversible-patch skill library) + **L3 Content** (Open-Ideation Gemmini DSE on MLPerf Tiny v1.3 streaming). Novelty hypotheses, evaluation thresholds, and publish/kill decisions all centralized at §4/§5/§5.3 of the overview spec (Codex 3-round review passed).

Superseded: [2026-04-17 single-loop spec](docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md) (archived 2026-04-19).

## Getting started

본 프로젝트는 **Operator 1명이 다중 에이전트(Researcher/Developer 역할)를 감독·운영하는 single-operator multi-agent 구조**다. 신규 참여자(=Operator)는 [`docs/onboarding.md`](docs/onboarding.md) 부터 시작한다 — Operator의 세 감독 채널(학습 · Researcher 위임 · Developer 위임) + 환경 준비 + 자주 쓰는 명령 + 작업 컨벤션이 한 곳에 정리되어 있다. 용어가 막히면 [`docs/glossary.md`](docs/glossary.md) 옆에 둔다.

## Current phase

**G0 bootstrap → G1** (program overview approved; L1/L2/L3 파생 spec 착수 단계).

| Gate | Description | Status |
|---|---|---|
| G0 | Program bootstrap (K1 52 + K2 61 sources + overview spec + 부수 문서 정리) | ✅ complete |
| G1 | L1 Process bootstrap (SHA-pinned Nix + Fargate Spot + `make run` gcd SFN 완주, KG-A~KG-E kill gates) | pending — L1 파생 spec |
| G2 | L2 Substrate (typed-frontmatter memory + `L2.memory.recall` graphify backend + reversible-patch skill library) | pending (L1 완료 후 병렬) |
| G3 | L3 Content MVP (Open-Ideation DSE on Gemmini, gcd/ibex/aes) | pending |
| G4 | 통합 실험 + 논문 figure (overview spec §5.3 publish/reframed/kill 결정) | pending |

**컨텍스트 관리 (2026-05-09부)**: `wiki/index.md` + 컴파일 페이지가 **default 라우팅**, graphify는 cross-component path 보조 — 자세히는 아래 [Knowledge base](#knowledge-base-wiki-first-hybrid-2026-05-09) 섹션.

## Knowledge base (wiki-first hybrid, 2026-05-09~)

**Default 컨텍스트 라우팅**은 `wiki/index.md` 기반 마크다운 위키. **보조**로 graphify가 cross-component path 쿼리를 담당. 근거는 [Karpathy LLM Wiki 72-run 벤치마크](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/) (wiki vs graphify: 토큰 −53.6%, 시간 −39.3%, 품질 +6%, p<0.01) — 본 프로젝트의 multi-source synthesis(K1/K2 paper 종합·spec 작성)가 정확히 wiki 우위 영역.

**전환 이력**: Phase 1a Wiki Skill Engine (S3 코드, 2026-04-17~22 폐기) → graphify-only ([adoption design](docs/superpowers/specs/2026-04-22-graphify-adoption-design.md), [evaluation](docs/superpowers/specs/2026-04-22-graphify-evaluation.md) S1 4/5 PASS) → **wiki-first hybrid** (2026-05-09~).

### 1. Default — wiki primary

```
wiki/
├── index.md            # 라우팅 카탈로그 (← 답변 시 1차 진입)
├── log.md              # ingest 이력
├── {slug}.md           # 컴파일 페이지 (concept · policy · synthesis · decision · entity)
└── raw/                # 불변 원본 (sessions · papers · blogs · repos · docs · benchmarks)
```

- 답변 작성 시 `[[페이지명]]` 인용 **강제**.
- 페이지 frontmatter `sources` / `related_specs` 명시 → spec 결정의 evidence 그래프 자동 형성.
- 컴파일 진척 (2026-05-09): **9 페이지** (Phase-0 sessions 4 → concept 4 + policy 1; K1 papers 4 → synthesis 4). K2 papers 4 (ε / ζ / η / θ) pending.
- 새 raw 노트 ingest는 `documentation:llm-wiki` skill의 5단계 워크플로 사용.

### 2. 보조 — graphify cross-component path

- **언제**: wiki에 답이 없거나 spec 결정 ↔ source paper 의존성 같은 그래프 탐색이 필요할 때.
- **명령**: `make graph-serve` (MCP 서버), `uv run graphify query "<question>"` (BFS), `graphify path "A" "B"` (최단 경로), `graphify explain "X"` (노드 설명).
- **인덱스**: `graphify-out/GRAPH_REPORT.md` (커뮤니티·god-node), `graphify-out/graph.json` (구조), `graphify-out/graph.html` (시각화).
- **업데이트**: `make graph-update` (AST 증분, LLM 비용 0), 전체 rebuild는 Claude Code 세션에서 `/graphify .`.
- **lint**: `make graph-lint` — orphan=0 / dangling=0 / AMBIGUOUS ≤ 0.3.

### 3. Layer 분리 (중요)

본 wiki-first 정책은 **human/LLM 컨텍스트 회수 layer**만 다룬다. agent system 내부 API인 `L2.memory.recall` / `L2.skill_library.query` / `L2.lint.check`는 [overview spec §3.2](docs/superpowers/specs/2026-04-19-integrated-research-program-design.md) + [L2-substrate-design §5.1](docs/superpowers/specs/2026-04-23-L2-substrate-design.md)에서 **graphify backend로 spec-freeze** — 변경은 L2 spec-owner Codex 3-round review를 거쳐야 한다.

### 4. 원본 자료 (raw seed)

- Project glossary: `docs/glossary.md`
- K1 direction report (52 sources 종합): `docs/knowledge-base/2026-04-19-k1-direction-report.md`
- K1 raw axes (52건): `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md` → wiki에 4 synthesis 페이지로 컴파일 완료
- K2 raw axes (61건, 2026-04-22): `wiki/raw/papers/k2-{epsilon,zeta,eta,theta}-*.md` → ingest pending
- Source index (decision_anchors · spec_contradictions · critical_read): `wiki/raw/imports_manifest.yaml`
- Operating rules: overview spec §7로 흡수 완료 (2026-04-19부 단일 진실원천, 별도 `wiki/program/` 디렉토리 없음).

## Phase 1a — Wiki Skill Engine (⛔ 엔진 코드 폐기, 위키 자체는 부활)

> 2026-04-22 graphify 전환으로 `src/semi_design_wiki/` **엔진 코드**는 폐기됐지만, 마크다운 위키 자체는 2026-05-09 wiki-first hybrid에서 부활 — 위 [Knowledge base](#knowledge-base-wiki-first-hybrid-2026-05-09) 섹션 참조. 아래 CLI 명령은 historical reference (대체 워크플로는 `documentation:llm-wiki` skill).

```bash
make install      # uv sync
make test         # pytest
# legacy (제거됨):
# uv run wiki-init --root wiki
# uv run wiki-sync --root wiki
# uv run wiki-lint --root wiki
```

## Learning (parallel)

Phase 0 curriculum (EDA operator lens): `docs/learning/phase-0-curriculum.md`. Q&A 불변 원본: `wiki/raw/sessions/`. **컴파일 진입점**: [`wiki/phase-0-eda-operator-lens.md`](wiki/phase-0-eda-operator-lens.md) (policy) — Branch A 4 concept 페이지([[cmos-fundamentals]], [[digital-logic-gates]], [[clock-and-timing]], [[fsm-and-pipeline]])로 라우팅.

## Open decisions

Tracked in [issues/](issues/README.md). 2026-04-19 재배치 완료 — 각 이슈는 L1/L2/L3 파생 spec 범위로 이관.
