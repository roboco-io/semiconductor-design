---
type: raw-import
axis: eta
title: "K2 축별 자료 — Reversible-patch skill library + structural mutation"
date: 2026-04-22
phase: K2
curator: claude-opus-4-7
source_count: 13
intent: "L2 skill library (Voyager-style, reversible-patch)와 L3 Open-Ideation의 template-breaking 구조 mutation(H1b non-knob structural patch) 설계 근거. 부록 C exclusion list 아닌 structural transform의 구체 오퍼레이터를 선행 문헌에서 추출."
tags: [k2, skill-library, mutation-operator, RL-for-chip, multi-agent]
---

# η. Reversible-patch skill library + structural mutation — K2 Resource Survey

## Resources

### 1. Voyager — Open-Ended Embodied Agent with Large Language Models (NeurIPS 2023)
- URL: https://arxiv.org/abs/2305.16291 · repo https://github.com/MineDojo/Voyager
- Authors: Wang, Xie, Jiang, Mandlekar, Xiao, Zhu, Fan, Anandkumar
- Tag: [foundational, skill-library, critical-read]
- WHAT: Ever-growing executable skill library 개념의 출발점. 스킬은 실행 가능한 JS 코드로 파일 시스템에 append-only 저장되며 self-verification 통과 시 등록된다. L2.skill_library의 원형이지만 **버전/리버스 롤백·patch DAG는 아직 없다** — η axis가 이 공백을 EDA 영역에서 메꾸는 것이 목표.

### 2. Evolving Programmatic Skill Networks — PSN (2026, arXiv 2601.03509)
- URL: https://arxiv.org/abs/2601.03509
- Authors: Shi, Yuan, Liu
- Tag: [recent-SOTA, skill-library, critical-read]
- WHAT: Voyager의 flat skill library를 Claude Opus 4.5로 offline-refactor하여 7개 generic + 20 wrapper + 38 unchanged로 계층 압축. **REFLECT 단계의 structured fault localization**과 **maturity-aware update gating**이 핵심 — L2 lint의 "skill deprecation" 정책 설계에 직접 참고.

### 3. SAGE — Reinforcement Learning for Self-Improving Agent with Skill Library (arXiv 2512.17102, 2025)
- URL: https://arxiv.org/abs/2512.17102
- Authors: Wang, Yan, Wang, Tian, Mishra, Xu, Gandhi, Xu, Cheong
- Tag: [recent-SOTA, skill-library, RL-for-chip]
- WHAT: Sequential Rollout로 이전 태스크에서 생성된 스킬이 다음 태스크에 누적 재사용되며, **Skill-integrated Reward**가 outcome reward를 보완해 효과적 스킬만 라이브러리에 남는다. AppWorld에서 step/token 감소 — reproducibility seed × 3 기준 설계 시 "RL이 자연스럽게 skill pruning을 수행하는 모델"의 참고.

### 4. Agent Skills for LLMs — Architecture, Acquisition, Security (arXiv 2602.12430, 2026 survey)
- URL: https://arxiv.org/abs/2602.12430
- Authors: Xu, Yan
- Tag: [survey, skill-library, critical-read]
- WHAT: 스킬을 "composable packages of instructions, code, and resources"로 공식화하고 획득 경로를 RL-with-skill-library / autonomous discovery / compositional synthesis 3축으로 분류. 26.1%의 커뮤니티 스킬에 취약점이 있음을 실증하고 **provenance → graduated deployment permission 4-tier governance**를 제안 — §7.2 blinded audit·signing 기준의 선행 사례.

### 5. SEAgent — Self-Evolving Computer Use Agent (arXiv 2508.04700, 2025)
- URL: https://arxiv.org/abs/2508.04700
- Tag: [recent-SOTA, skill-library]
- WHAT: World State Model로 trajectory를 step-wise 평가하고 Curriculum Generator가 점진적으로 난도 상승 태스크를 생성. 실패 액션에 대한 adversarial imitation + 성공 액션 GRPO로 정책 갱신 — Voyager auto-curriculum의 최신 형태. OSWorld 5개 신규 소프트웨어에서 11.3%→34.5% 성공률.

### 6. EXIF — Automated Skill Discovery through Exploration and Iterative Feedback (arXiv 2506.04287, 2025)
- URL: https://arxiv.org/abs/2506.04287
- Authors: Yang, Kang, Lee, Lee, Yun, Lee
- Tag: [skill-library, recent-SOTA]
- WHAT: Explorer agent(Alice)가 환경을 탐색해 feasible, environment-grounded skill dataset을 생성하고, Target agent(Bob)의 성능 gap에 따라 탐색을 조정하는 이중 agent 루프. 동일 base model만으로도 Webshop·Crafter에서 유의미한 개선 — EDA tool(OpenROAD·Yosys)에 적용 시 **Alice가 실패 리포트를 보고 스킬 갭을 메우는 구조** 참고.

### 7. SEVerA — Verified Synthesis of Self-Evolving Agents (arXiv 2603.25111, 2026)
- URL: https://arxiv.org/abs/2603.25111
- Authors: Banerjee, Xu, Singh
- Tag: [recent-SOTA, skill-library, critical-read]
- WHAT: Planner LLM이 agent program을 합성하되 **Formally Guarded Generative Models**가 출력 계약을 강제 — verified rejection sampling으로 제약 위반 0. **Reversible-patch에 formal guard를 붙이는 가장 최근 frame** — η 스킬 등록 시 "DRC clean + STA positive slack" 계약을 formal guard로 인코딩하는 설계 근거.

### 8. EvolVE — Evolutionary Search for LLM-based Verilog Generation (arXiv 2601.18067, 2026)
- URL: https://arxiv.org/abs/2601.18067
- Authors: Hsin, Deng, Hsieh, Huang, Hung
- Tag: [recent-SOTA, mutation-operator, critical-read]
- WHAT: MCTS(기능 정확성) vs Idea-Guided Refinement(최적화) 비교 + Structured Testbench Generation. IC-RTL industry-scale 벤치에서 최대 66% PPA 감소. **단 abstract 수준에서는 "structural vs parametric mutation 구분이 명시적이지 않음"** — η axis는 IGR를 "non-knob patch"로 정제해 exclusion list 준수 여부를 lint로 검증하는 것이 차별점.

### 9. Marco — Configurable Graph-Based Multi-AI Agents Framework for Hardware Design (NVIDIA, arXiv 2504.01962, 2025)
- URL: https://arxiv.org/abs/2504.01962 · https://research.nvidia.com/publication/2025-06_marco-configurable-graph-based-task-solving-and-multi-ai-agents-framework
- Tag: [multi-agent, recent-SOTA]
- WHAT: Layout 최적화 / Verilog·DRC 코딩 / MCMM 타이밍 분석을 graph-based task-solving으로 통합. MCMM timing agent 60× 가속, path debug 86% 해결. **L1 Fargate Map 분할 + L2 skill DAG 조합 설계 시 산업 레퍼런스**.

### 10. Retrieve, Schedule, Reflect — LLM Agents for Chip QoR Optimization (arXiv 2603.13767, 2026)
- URL: https://arxiv.org/abs/2603.13767
- Authors: Ouyang, Luo, Zuo, Ma
- Tag: [multi-agent, RL-for-chip]
- WHAT: RAG로 전문가 지식 search tree를 구성하고 Pareto-driven feedback + language reflection으로 스케줄링. RL 대비 10% 타이밍 향상·4× 속도. **ORFS-agent(2025)와 동류 계열** — η는 여기서 "knob scheduling"을 넘어 **structural patch를 스킬로 승격**하는 한 단계 위 작업.

### 11. MACO — Multi-Agent LLM Hardware/Software Co-Design for CGRAs (arXiv 2509.13557, 2025)
- URL: https://arxiv.org/abs/2509.13557
- Authors: Jiang, Sun, Zhong, Krishna, Patil, Tan, Zhang
- Tag: [multi-agent]
- WHAT: Co-design / Error Correction / Best-Design Selection / Eval-Feedback 4단계 iterative 루프 + exponentially decaying exploration + LLM self-learning. CGRA는 Gemmini보다 구조 자유도가 커 **"structural mutation"이 어떻게 H/W-S/W 공간을 함께 움직이는지**의 사례로 유용.

### 12. AlphaChip Nature addendum + "That Chip Has Sailed" 반박 (DeepMind 2024, arXiv 2411.10053)
- URLs: https://deepmind.google/discover/blog/how-alphachip-transformed-computer-chip-design/ · https://arxiv.org/abs/2411.10053
- Tag: [foundational, RL-for-chip]
- WHAT: 2024-09 Nature addendum로 pre-trained checkpoint 공개. TPU v5e 10 블록/−3.2% wire length → Trillium 25 블록/−6.2%로 세대별 개선, MediaTek이 Dimensity Flagship 5G에 확장 채택. **RL이 chip placement에 "patch-based" 개입을 반복 적용하는 계열의 기준선** — 단, η axis는 placement가 아닌 **RTL 단계 structural transform**을 겨냥.

### 13. SISA — Scale-In Systolic Array for GEMM Acceleration (arXiv 2603.29913, 2026)
- URL: https://arxiv.org/abs/2603.29913
- Tag: [mutation-operator, recent-SOTA]
- WHAT: 정사각형 systolic array를 가로 rectangular slab으로 분할, 작은/skewed matrix에 대해 독립 스케줄링을 허용하면서 대형 GEMM 시 full-array 능력 유지. 최대 8.52× 속도·93% EDP 감소 — **Gemmini 부록 C.1 exclusion list(meshRows/meshColumns knob)를 벗어나는 structural patch 오퍼레이터**(예: "array-partitioning transform")의 구체 prior.

### (배경 참고 — 본문 카운트 외)
- Koza, *Genetic Programming* (MIT Press, 1992/1994) — HDL 진화의 개념적 선조. rewrite-rule 기반 circuit synthesis. η는 LLM-guided mutation이 GP의 structural operator에 수렴함을 전제.
- PIT · Mothra — SW mutation testing 도구. 하드웨어 "reversible patch" 개념과는 직접 연결이 약하지만, **mutation → kill / survive 판정 프레임이 L2 lint의 "skill acceptance gate"로 전이 가능**하다는 아이디어의 선행.

## Landscape Snapshot

- **Converged**:
  Voyager 계열 executable skill library는 2023→2026에 survey 수준으로 안착(AgentSkills 2602.12430). RL 기반 skill pruning(SAGE), auto-curriculum(SEAgent), explorer–target 이중 루프(EXIF)가 서로 수렴. Chip design 측에서는 multi-agent graph scheduler(MARCO, RSR, MACO)가 **knob/flow 레벨 agent 협업**으로 거의 commodity화.

- **Still open**:
  1. **Reversible-patch 형식**: 스킬을 "DRC·STA·LEC 계약이 붙은 reversible transform"으로 버전 관리하는 공개 연구가 아직 드물다. SEVerA(2603.25111)가 가장 근접.
  2. **Non-knob structural patch 카탈로그**: EvolVE IGR나 SISA의 slab partitioning, MACO의 CGRA 재구성 같은 transform을 **exclusion list(부록 C) 바깥의 operator로 통일된 taxonomy로 수집한 자료가 없음**.
  3. **Skill deprecation / audit 정책**: AgentSkills 26.1% 취약점 수치는 존재하지만 EDA 맥락의 blinded audit(§7.2)과 매핑된 사례가 없음.

- **η axis에서의 novelty surface**:
  1. L2.skill_library를 **"Voyager × SEVerA × RSR"의 교집합** — executable skill + formal guard + Pareto reflection — 으로 정의해 `wiki/skills/` 아래 append-only로 운용.
  2. L3 Open-Ideation은 **EvolVE IGR 계열 mutation을 "부록 C exclusion 미준수 시 자동 reject"하는 lint**로 감싸 H1b(non-knob structural patch)를 정량 지표화.
  3. 스킬 등록 기준은 reproducibility seed × 3 + blinded audit을 **AgentSkills 4-tier permission**에 매핑해 L2 governance로 채택.

  **Karpathy-wiki(δ) · Voyager skill library(이 η) · EvolVE mutation(α) 삼자를 EDA 리포트 아티팩트로 엮으면, 상용 PPA 경쟁이 아니라 "재사용·역전 가능한 구조 transform 카탈로그"라는 학술/프로세스 novelty가 성립한다.**
