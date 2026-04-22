# semiconductor-design

AI-agent research for open-source EDA + DL accelerator design — **Report-Grounded Vibe-Coded AutoResearch** (통합 프로그램, 2026-04-19).

## Program overview

See [통합 프로그램 overview spec](docs/superpowers/specs/2026-04-19-integrated-research-program-design.md) for the authoritative design. 3-layer 구조 — **L1 Process** (SHA-pinned Nix + AWS Fargate Spot) + **L2 Substrate** (report-grounded memory + reversible-patch skill library) + **L3 Content** (Open-Ideation Gemmini DSE on MLPerf Tiny v1.3 streaming). Novelty hypotheses, evaluation thresholds, and publish/kill decisions all centralized at §4/§5/§5.3 of the overview spec (Codex 3-round review passed).

Superseded: [2026-04-17 single-loop spec](docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md) (archived 2026-04-19).

## Current phase

**G0 bootstrap** (program overview approved; L1/L2/L3 파생 spec 착수 준비).

| Gate | Description | Status |
|---|---|---|
| G0 | Program bootstrap (K1 지식 수집 + overview spec + 부수 문서 정리) | 🟡 near-complete |
| G1 | L1 Process bootstrap (SHA-pinned Nix + Fargate Spot + `make run` gcd SFN 완주, KG-A~KG-E kill gates) | pending |
| G2 | L2 Substrate (graphify 기반 graph knowledge index + reversible-patch skill library) | pending (L1 완료 후 병렬) |
| G3 | L3 Content MVP (Open-Ideation DSE, gcd/ibex/aes) | pending |
| G4 | 통합 실험 + 논문 figure (§5.3 publish/reframed/kill 결정) | pending |

## Knowledge base (graphify 기반, 2026-04-22~)

1차 탐색 경로는 **graphify** v0.4.25 기반 지식 그래프다. Phase 1a wiki 엔진은 폐기 예정 — 전환 근거는 [`docs/superpowers/specs/2026-04-22-graphify-adoption-design.md`](docs/superpowers/specs/2026-04-22-graphify-adoption-design.md), 평가 결과는 [`docs/superpowers/specs/2026-04-22-graphify-evaluation.md`](docs/superpowers/specs/2026-04-22-graphify-evaluation.md) (S1 4/5 PASS).

- **Graph 인덱스**: `graphify-out/GRAPH_REPORT.md` (커뮤니티·god-node 요약), `graphify-out/graph.json` (구조), `graphify-out/graph.html` (대화형 시각화)
- **탐색 명령**: `graphify query "<question>"` (BFS), `graphify path "A" "B"` (최단 경로), `graphify explain "X"` (노드·이웃 설명)
- **업데이트**: `make graph-update` (AST 증분, LLM 비용 0), 전체 rebuild는 Claude Code 세션에서 `/graphify .` 또는 skill.md 레시피 수동 실행
- **lint**: `make graph-lint` — orphan=0, dangling=0, AMBIGUOUS ≤ 0.3

**원본 자료 (graphify seed corpus)**

- Project glossary: `docs/glossary.md`
- K1 direction report: `docs/knowledge-base/2026-04-19-k1-direction-report.md`
- K1 raw sources (52건): `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md`
- Source index: `wiki/raw/imports_manifest.yaml`
- Operating rules (graphify 전환 후 overview spec §7에 흡수 예정): `wiki/program/{program,scoring,promotion_policy}.md`

## Phase 1a — Wiki Skill Engine (⛔ 폐기 예정, S3에서 제거)

> 2026-04-22부로 graphify로 전환. 아래 명령은 legacy — 신규 지식 조회는 `graphify query` 또는 `GRAPH_REPORT.md`를 사용.

```bash
make install      # uv sync
make test         # pytest
# legacy (폐기 예정):
# uv run wiki-init --root wiki
# uv run wiki-sync --root wiki
# uv run wiki-lint --root wiki
```

## Learning (parallel)

Phase 0 curriculum (EDA operator lens): `docs/learning/phase-0-curriculum.md`. Q&A sessions: `wiki/raw/sessions/`.

## Open decisions

Tracked in [issues/](issues/README.md). 2026-04-19 재배치 완료 — 각 이슈는 L1/L2/L3 파생 spec 범위로 이관.
