---
title: "K1-β: Agentic EDA + Autotuning + ML for Chip Flows — Direction Evidence"
type: synthesis
tags: [k1, agentic-eda, autotuning, rl-for-chip, novelty-window, orfs-agent]
status: active
confidence: medium
created: 2026-05-09
updated: 2026-05-09
sources:
  - raw/papers/k1-beta-agentic-eda.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # H1b · §3 L1
  - docs/eda_agent_handoff.md  # superseded — ORFS-agent로 인해 autotuning MVP 무효
  - docs/knowledge-base/2026-04-19-k1-direction-report.md
---

# K1-β: Agentic EDA — Direction Evidence

본 프로젝트의 **autotuning MVP가 무효화되고 H1b "structural patch" 트랙으로 reframe** 된 결정의 1차 근거. 12개 source 중 **ORFS-agent(2025)** 가 그 자체로 reframe trigger.

## Reframe Trigger — ORFS-agent (source #1)

| 항목 | 값 |
|------|----|
| 성능 | ASAP7/SKY130HD에서 ORFS AutoTuner BO baseline 대비 **wirelength/effective-clock-period ~13% 개선, 실행 횟수 ~40% 감소** |
| 방식 | Model-agnostic LLM agent + function calling + METRICS2.1 read로 bad config skip |
| 의미 | **본 프로젝트의 기존 ORFS autotuning MVP 가설이 이미 cover됨.** 동일 영역에서 incremental 개선은 publishable 불가. → spec §H1a single-track autotuning이 **§H1b structural patch + AutoResearch process**로 이동. |

## 핵심 Landscape

| 영역 | 상태 | 시사점 |
|------|------|--------|
| Pure parameter-sweep autotuner (BO/TuRBO/RL wrapper) | **포화** — 14번째 tuner는 incremental | 본 프로젝트 단독 MVP로 부적합 |
| LLM agent가 EDA tool을 function-call로 운영 | ORFS-agent + AutoEDA(MCP-based) 등장 | baseline·infra로 채택 |
| `.rpt` (DRC/STA/LEC) 읽고 **targeted patch** 제안 | **미해결** | H1b의 직접 타겟 |
| Cross-design memory (candidate N이 N−1에서 학습) | 대부분 시스템 memoryless | L2 substrate의 differentiation seed |
| **Spec→RTL critique pre-synthesis** | 미해결 | §검증 axis 보조 |
| Template DSE에서 벗어나 microarch 제안 | **미해결** | H1b "non-knob structural patch" 정합 |
| AlphaChip 재현성 논쟁 | False Dawn vs Sailed 양측 | 본 프로젝트는 RL-for-placement 회피, agent-led ideation으로 우회 |
| 상용 copilot (Cadence Cerebrus / Synopsys DSO.ai / Siemens Solido) | DAC 2025 모두 "agentic" 포지셔닝, Cerebrus 1000+ 테이프아웃 | **오픈소스 differentiation urgency↑** |

## Source 카테고리

### Agentic SOTA (3종 — 본 프로젝트가 비교될 baseline)
- **ORFS-agent** (2025): function-call + METRICS2.1, autotuning MVP를 무효화한 결정적 source.
- **AutoEDA** (2025/2026): MCP server로 EDA tool wrap, fine-tuned local agent. 9.9× accuracy, 97% token 감소.
- **Survey "Dawn of Agentic EDA"** (2026): Neural-Augmented Solvers vs Agentic Orchestrators 분류. Perception/Cognition/Action stack 프레임.

### Autotuner Foundation (3종 — ceiling reference)
- **ORFS AutoTuner + METRICS2.1**: canonical open harness, ORFS-agent의 baseline.
- **AutoDMP** (NVIDIA ISPD 2023): GPU 가속 DREAMPlace + MOTPE, 2.7M cells/320 macros 3h.
- **PTPT / RankTuner / MO-TuRBO** bundle: BO·trust-region·ranking 계열 한도.

### RL-for-chip 논쟁 (3종 — H1b가 회피해야 할 함정)
- **AlphaChip** (Nature 2021 + 2024 Addendum): RL floorplan 원조.
- **False Dawn** (CACM 2024): 독립 재구현 시 SOTA 미달, 비판.
- **Sailed** (2024): Google의 point-by-point 반박.
- 시사: small team이 RL-for-placement에 깊이 들어가면 재현성 늪. **agent-led ideation으로 우회.**

### Dataset / Foundation (1종)
- **CircuitNet 2.0** (ICLR 2024): 10k+ designs @ 14nm, routability/IR-drop/timing 라벨. ML-for-EDA의 de-facto 데이터셋.

### 도메인 LLM (1종)
- **ChipNeMo** (α와 중복): 후속 agent work들의 전제 — EDA script gen, bug triage.

### 상업 압력 (1종)
- **Cerebrus / DSO.ai / Solido**: DAC 2025에 모두 agentic. **오픈 솔루션이 reasoning trace + reproducibility로 차별화해야 publishable**.

## 본 프로젝트와의 연결 (Direction Evidence)

### Reframe된 H1b가 가리키는 3개 novelty window

| # | Window | 본 프로젝트 매핑 |
|---|--------|------------------|
| 1 | Karpathy-style open-ideation loop **on top of** ORFS-agent (parameter vector → structural variant) | spec §3 L3 Content "Open Ideation" 트랙 |
| 2 | **Report-grounded agent debugging** — `.rpt` 입력 → next-action 데이터셋·eval | spec §3 L2 substrate `skill_library` + `memory.recall()` |
| 3 | Multi-candidate evolutionary DSE를 **AutoResearch artifact**로 frame (PPA 수치보다 reasoning trace) | spec §1 intent "academic/process novelty" 직접 충족 |

### 핵심 결정 영향

| 결정 | K1-β 근거 |
|------|-----------|
| autotuning 단독 MVP 폐기, structural patch로 pivot | source #1 ORFS-agent ~13%/-40% (=ceiling) |
| ORFS-agent를 **baseline + infra**로 채택 (재구현 X) | source #1 + #4 open-source 가용 |
| RL-for-placement 회피 | source #6/#7/#8 재현성 논쟁 |
| reasoning trace를 1차 deliverable로 | source #3 + #12 (오픈 vs 상용 차별화) |
| METRICS2.1 + `.rpt` parsing을 L2 메모리 schema로 | source #1, #2 (function-call·MCP 패턴) |

## 미해결 / 추가 탐색

- **Open Ideation의 "structural patch" 정의 범위** — Gemmini knob을 어디까지 허용하고 어디부터 spec §부록 C exclusion 해야 publishable인지 G2 직전 결정.
- **Evolution algorithm 선택** — α의 EvolVE는 MCTS vs Idea-Guided 비교. 본 프로젝트가 어느 쪽을 채택/혼합할지는 G3 직전 결정.
- **AutoEDA의 MCP 서버 패턴 채택 가능성** — 본 프로젝트의 Tool plane을 MCP로 표준화할지 (현재 Python wrapper만).

## 교차 참조

- [[k1-alpha-llm-for-hdl-evidence]] — RTL 생성 축의 SOTA·CVDP-agentic novelty seam과 본 페이지의 reframe이 정확히 동일 방향 가리킴
- [[clock-and-timing]] — `.rpt` slack의 출처
- [[fsm-and-pipeline]] — "structural patch"의 단위(파이프 깊이/너비, systolic 차원)
- [[phase-0-eda-operator-lens]] — `.rpt` 해석 능력이 본 페이지 적용의 전제
- (pending) `[[k1-gamma-opensource-eda-evidence]]` — Yosys/OpenROAD 도구 layer
- (pending) `[[k1-delta-research-memory-evidence]]` — Karpathy AutoResearch + memory 패러다임
- [[k2-zeta-l1-runtime-evidence]] — ORFS-agent reframe이 LibreLane 3.0.2 + Fargate Spot L1 runtime으로 구체화 (§6.2 lockfile + KG-A~KG-E)

## Source

- 원본: `raw/papers/k1-beta-agentic-eda.md` (2026-04-19 collected, confidence: low → medium)
- 12개 외부 paper의 decision_anchors는 `raw/imports_manifest.yaml`
- 본 페이지의 reframe 결정은 `docs/eda_agent_handoff.md`(superseded) → `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` 채택 경로에 기록
