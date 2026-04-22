---
title: graphify S1 평가 리포트
status: passed
date: 2026-04-22
verdict: 4/5 PASS — S2 진행
related:
  - docs/superpowers/specs/2026-04-22-graphify-adoption-design.md
  - docs/superpowers/plans/2026-04-22-graphify-adoption.md
---

# graphify S1 평가 리포트

## 1. K1 핵심 개념 20개 (ex-post 합리화 방지 — 평가 전 고정)

<!--
  선정 주체: codex (headless `codex exec`, 2026-04-22) — Claude 편향과 독립적 관점 확보 목적.
  분포: α 4 · β 4 · γ 5 · δ 3 · 공통 4 = 20.
  이 목록은 평가 시작(Task 3 graphify 스캔) 전에 고정된다. 이후 수정 금지.
  graphify가 이 개념들을 얼마나 노드로 추출하는지가 M2 채점의 분모.
-->

1. **CVDP** — 축: α · 근거: `wiki/raw/papers/k1-alpha-llm-for-hdl.md` · 설명: RTL reuse·verification 등 agentic HDL 난제를 포함하며 SOTA 34% pass@1로 novelty가 남은 핵심 벤치마크.
2. **VerilogEval** — 축: α · 근거: `wiki/raw/papers/k1-alpha-llm-for-hdl.md` · 설명: HDL 생성 연구의 사실상 표준 pass@k 벤치마크로, 포화 영역을 판별하는 기준점.
3. **RTLLM** — 축: α · 근거: `wiki/raw/papers/k1-alpha-llm-for-hdl.md` · 설명: 자연어 spec·reference RTL·testbench·PPA 평가를 포함하는 대표 RTL 생성 벤치마크.
4. **EvolVE** — 축: α · 근거: `wiki/raw/papers/k1-alpha-llm-for-hdl.md` · 설명: Idea-Guided Refinement와 template-breaking 구조 탐색을 연결하는 Open-Ideation의 직접 선행 개념.
5. **ORFS-agent** — 축: β · 근거: `wiki/raw/papers/k1-beta-agentic-eda.md` · 설명: OpenROAD-flow-scripts를 LLM agent가 구동한 최신 baseline이며 본 프로그램이 넘어서야 할 직접 비교 대상.
6. **METRICS2.1** — 축: β · 근거: `wiki/raw/papers/k1-beta-agentic-eda.md` · 설명: ORFS-agent가 bad config를 건너뛰는 데 사용한 report-level metric 포맷으로 report-grounded loop의 출발점.
7. **ORFS AutoTuner** — 축: β · 근거: `wiki/raw/papers/k1-beta-agentic-eda.md` · 설명: Ray Tune 기반 canonical open-source parameter tuning harness이며 ORFS-agent가 이긴 BO baseline.
8. **AutoEDA** — 축: β · 근거: `wiki/raw/papers/k1-beta-agentic-eda.md` · 설명: MCP 기반 EDA tool 서버와 LLM agent orchestration을 결합한 agentic EDA 대표 사례.
9. **LibreLane 2.4** — 축: γ · 근거: `wiki/raw/papers/k1-gamma-opensource-eda.md` · 설명: OpenLane2의 후속 canonical flow로, Efabless shutdown 이후 프로젝트의 RTL-to-GDSII 기준 스택.
10. **OpenROAD** — 축: γ · 근거: `wiki/raw/papers/k1-gamma-opensource-eda.md` · 설명: sign-off feedback과 PnR report를 생성하는 핵심 open-source physical design tool.
11. **sky130A** — 축: γ · 근거: `wiki/raw/papers/k1-gamma-opensource-eda.md` · 설명: open_pdks 기반 130nm PDK로, 절대 7nm PPA 비교 불가라는 실험 경계를 고정한다.
12. **Gemmini** — 축: γ · 근거: `wiki/raw/papers/k1-gamma-opensource-eda.md` · 설명: Open-Ideation DSE의 주 대상인 Berkeley systolic array generator이며 Chipyard 기반 accelerator template.
13. **MLPerf Tiny v1.3** — 축: γ · 근거: `wiki/raw/papers/k1-gamma-opensource-eda.md` · 설명: streaming wakeword·duty-cycle·energy metric을 포함한 L3 평가의 외부 yardstick.
14. **Karpathy LLM Wiki** — 축: δ · 근거: `wiki/raw/papers/k1-delta-research-memory.md` · 설명: raw sources → LLM-maintained wiki → schema라는 compounding knowledge base 패턴의 원형.
15. **Voyager** — 축: δ · 근거: `wiki/raw/papers/k1-delta-research-memory.md` · 설명: executable skill library와 self-verification을 결합한 reversible-patch memory의 canonical precedent.
16. **A-MEM** — 축: δ · 근거: `wiki/raw/papers/k1-delta-research-memory.md` · 설명: Zettelkasten식 dynamic linking과 memory evolution으로 wiki-scale lint-and-rewire 문제에 가장 가까운 학술 analog.
17. **L1 Process** — 축: 공통 · 근거: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` · 설명: SHA-pinned reproducibility bundle과 AutoResearch harness를 담당하는 실행 substrate.
18. **L2 Substrate** — 축: 공통 · 근거: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` · 설명: report-grounded memory와 reversible-patch skill library를 제공하는 본 graphify 전환의 핵심 layer.
19. **L3 Content** — 축: 공통 · 근거: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` · 설명: Gemmini와 MLPerf Tiny 기반 Open-Ideation DSE를 수행하는 실험 content layer.
20. **H1b Non-knob structural patch** — 축: 공통 · 근거: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` · 설명: 단순 parameter tuning이 아닌 sign-off clean RTL/constraint transform을 세는 primary novelty metric.

## 2. 실행 로그 (단일 전체 repo 스캔)

> **설계 변경 (2026-04-22)**: 4-corpus 분리 스캔은 graphify CLI 실제 동작(spec §1.3) 확인 후 폐기. 단일 전체 repo 1회 스캔으로 M1~M5 모두 평가.

### 2.1 Detect
- command: `graphify.detect.detect(Path('.'))`
- total_files: **93** (code 60, document 33, paper 0, image 0, video 0)
- total_words: 80,599
- skipped_sensitive: 0

### 2.2 AST 추출 (Part A, deterministic)
- command: `graphify.extract.extract(code_files, cache_root=...)`
- runtime: **0.80s**
- nodes produced: 307
- edges produced: (included in subsequent build)
- LLM cost: $0 (deterministic tree-sitter)

### 2.3 Semantic 추출 (Part B, 2 subagents parallel)
- dispatch: 2 × `Agent(subagent_type="general-purpose", model="opus")`
- chunk 1 (17 files: README·AGENTS·CLAUDE + wiki/program + wiki/raw + docs/glossary·eda_handoff·learning):
  - 125 nodes, 150 edges, 3 hyperedges
  - tokens: 118,557
  - duration: 347s (~5.8min)
- chunk 2 (16 files: k1-direction-report + docs/superpowers/{plans,specs} + issues):
  - 103 nodes, 117 edges, 3 hyperedges
  - tokens: 170,669
  - duration: 292s (~4.9min)
- parallel wall time: ~5.8 min (max of two)
- Claude Code subscription 기반 — per-token billing 없음

### 2.4 Build + Cluster + Export
- `build([ast, semantic])`: 547 nodes, 757 edges (warning: 66개 `file_type='concept'` 검증 경고 — 허용됨)
- `cluster(G)`: 55 communities (Leiden)
- `score_all(G, communities)`: cohesion scores
- `god_nodes(G, top_n=10)` + `surprising_connections(top_n=5)` + `attach_hyperedges`
- `to_json` + `to_html` + `report.generate` → `graphify-out/{graph.json, graph.html, GRAPH_REPORT.md}`
- 파일 크기: graph.html 438KB · graph.json 523KB · GRAPH_REPORT.md 20KB
- elapsed: <5s

### 2.5 Trench 분포 (node → file prefix 기준)
- code (src/·cdk/·tests/): 301
- narrative (wiki/raw/): 75
- spec (docs/superpowers/specs/): 56
- doc_other (기타 docs/·issues/): 49
- plan (docs/superpowers/plans/): 27
- contract (wiki/program/): 18
- root_doc (README/AGENTS/CLAUDE): 18
- other: 3

## 3. 지표

| # | 지표 | 합격선 | 실측 | Pass/Fail |
|---|------|-------|------|-----------|
| M1 | `src/semi_design_wiki/` 5 모듈 + 주요 함수(`sync_index.regenerate`, `lint_wiki.check`, `frontmatter.parse_file`) 노드화 | 3/3 함수 노드 존재 | `sync_index`·`lint_wiki`·`parse_file` 전부 graph.json 내 존재(god-node top 5에 `sync_index()`·`lint_wiki()`) | **PASS** |
| M2 | K1 핵심 개념 20개(§1) 중 node 존재 | ≥16/20 | 20/20 (완전 커버) | **PASS** |
| M3 | inter-trench edge 수 ÷ 3 trench 합산 node 수 (narrative+contract+code) | ≥ 0.5 | 0.000 (inter-trench edges 0건 / nodes_in_3 394) | **FAIL** |
| M4 | Leiden 커뮤니티 중 K1 α/β/γ/δ 축과 육안 매칭 | ≥ 1개 | Community 6 = "K1 β. Agentic EDA" (size 25), Community 12 = "K1 γ. Open-Source EDA Stack" (size 19) — 2개 매칭 | **PASS** |
| M5 | 전체 스캔 비용 / 시간 | < $5 / < 10분 | wall time ~6 min (Part B 2-subagent 병렬 5.8min + AST 0.8s + build/cluster/export <5s). Claude Code subscription 기반이라 per-token billing 없음 | **PASS** |

## 4. God-node + 정성 리뷰

### 4.1 God-nodes (degree/centrality 상위 5)
1. **Spec** (community 0 label) — "integrated research program design" spec 노드로, 프로그램 전체의 허브 역할
2. **sync_index()** — wiki engine의 중심 함수. `lint_wiki()`와 결합해 M1의 "sync_index.regenerate" 합격 근거
3. **lint_wiki()** — frontmatter·wikilink 검증 함수. graphify가 AST로 정확히 포착
4. **K1 γ. Open-Source EDA Stack + Accelerator Templates survey** — γ 축 최상위 노드, Leiden 커뮤니티 12 중심
5. **Project glossary** — `docs/glossary.md`의 용어 정의 노드, 여러 개념을 연결하는 허브

### 4.2 Hyperedges (주목할 만한 패턴)
- `three_layer_program_decomposition` (L1/L2/L3) — CLAUDE.md 기반, EXTRACTED 0.95
- `k1_four_axis_knowledge_survey` (α/β/γ/δ) — README.md 기반, EXTRACTED 0.95
- `phase0_branch_a_completion_path` (A1→A2→A3→A4) — 학습 커리큘럼 순서 포착
- `three_seam_convergence` (Seam A/B/C → integrated program) — K1 direction report 기반
- `h1_hypothesis_trio` (H1a/H1b/H1c + H1_primary + canonical decision table) — 가설 앙상블 정확히 포착
- `shared_entrypoint_contract` (orfs/librelane/metric-collector 3 image ← run-stage.sh) — L1 phase C Docker 설계 포착

### 4.3 M3 실패 원인 분석 (중요 finding)

inter-trench edge = **0**. 즉 graphify가 narrative(K1 논문) ↔ code(src/) ↔ contract(wiki/program) 간 연결을 하나도 만들지 못함.

**원인**: Part B subagent dispatch의 **chunk 경계**가 cross-trench 엣지 생성을 구조적으로 차단.
- chunk 1 subagent = narrative + contract + root_doc만 봄
- chunk 2 subagent = spec + plan + issues만 봄
- **code trench(301 nodes)는 AST-only로 처리 — subagent가 의미 엣지 추가 못함**
- AST 엣지는 code 내부로만 한정 (import/call/contains 등)

즉 "K1 알파의 ChipGPT" 개념 노드(narrative)가 "tests/conftest.py" 코드 노드(code)와 연결될 수가 없었다. 이는 **graphify chunk 전략의 설계적 한계**.

**완화책 (S3 이후 선택지)**:
- 옵션 A: chunk 단위를 더 크게 (1 chunk = 전체) 하여 single subagent가 전체를 봄 → context 길이 제약(80K words)
- 옵션 B: 2차 merge pass — 모든 chunk 결과 수집 후 또 다른 subagent가 "cross-chunk relationships" 전용 추출
- 옵션 C: Manifest/hyperedge 정책으로 보완 — spec에 cross-trench 관계를 명시적으로 기록
- 옵션 D: M3 지표 자체를 재정의 — graphify의 기본 동작에서는 cross-trench edge가 기대치를 낮춰야

본 평가 단독으로 옵션 결정 불필요. S2 이후 L2.lint 기준(graph integrity check)과 무관하므로 S2 진행 차단 사유 아님.

### 4.4 Leiden community 정밀 관찰
- **55 communities** 중 상위 8개가 size ≥ 20 (전체 노드의 ~60% 포함)
- α(K1-alpha LLM-for-HDL)과 δ(research memory)는 Community 3 "K1 Core Concepts 20"으로 merge — 본 평가에서 지정한 20개 개념이 서로 밀접하게 엮여 하나의 커뮤니티로 인식됨
- 이는 Leiden의 **modularity optimization** 특성상 정상 — 개별 축 구분이 아닌 "핵심 개념 묶음"으로 보는 관점

## 5. 판정

- [x] M1~M5 중 4/5 합격 (M3만 FAIL) → **S2 진행**
- [ ] M1~M3 중 2개 이상 미달 → 해당 없음 (1개 미달)
- [ ] M5만 미달 → 해당 없음

**판정 결과: 4/5 PASS — S2 Spec Revise 진행**

M3 FAIL은 graphify chunk 전략의 구조적 한계에서 비롯된 것으로, 채택 철회 사유가 아니며 §4.3 옵션 중 하나로 완화 가능. S2에서 overview spec 개정 시 cross-trench 엣지 부재를 L2 contract에서 명시적으로 고려 권고.
