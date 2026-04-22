---
title: graphify S1 평가 리포트
status: in-progress
date: 2026-04-22
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

## 2. 실행 로그

### 2.1 corpus-narrative (wiki/raw/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.2 corpus-contract (wiki/program/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.3 corpus-code (src/)
- command:
- runtime:
- node count:
- edge count:
- API cost:

### 2.4 corpus-all (repo root)
- command:
- runtime:
- node count:
- edge count:
- API cost:

## 3. 지표

| # | 지표 | 합격선 | 실측 | Pass/Fail |
|---|------|-------|------|-----------|
| M1 | `src/semi_design_wiki/` 5 모듈 + 주요 함수(`sync_index.regenerate`, `lint_wiki.check`, `frontmatter.parse_file`) 노드화 | 3/3 함수 노드 존재 | | |
| M2 | K1 핵심 개념 20개(§1) 중 node 존재 | ≥16/20 | | |
| M3 | inter-trench edge 수 ÷ 3 trench 합산 node 수 | ≥ 0.5 | | |
| M4 | Leiden 커뮤니티 중 K1 α/β/γ/δ 축과 육안 매칭 | ≥ 1개 | | |
| M5 | 전체 스캔 비용 / 시간 | < $5 / < 10분 | | |

## 4. God-node 정성 리뷰 (top 5)

## 5. 판정

- [ ] M1~M5 중 ≥4개 합격 → S2 진행
- [ ] M1~M3 중 2개 이상 미달 → graphify 채택 철회, 사용자 재질의
- [ ] M5만 미달 → 비용 최적화 후 S1 재시도

판정 결과: TBD
