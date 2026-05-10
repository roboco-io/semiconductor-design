---
title: "K2-η: Reversible-Patch Skill Library + Structural Mutation — Direction Evidence"
type: synthesis
tags: [k2, skill-library, mutation-operator, voyager, reversible-patch, structural-transform, h1b]
status: active
confidence: medium
created: 2026-05-10
updated: 2026-05-10
sources:
  - raw/papers/k2-eta-patch-mutation.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # H1b · §3.2 L2.skill_library · §7.2 blinded audit · 부록 C exclusion
  - docs/superpowers/specs/2026-04-23-L2-substrate-design.md  # skill registration governance
  - docs/superpowers/specs/2026-04-26-L3-content-design.md  # L3 Open-Ideation mutation
---

# K2-η: Reversible-Patch + Structural Mutation — Direction Evidence

본 프로젝트의 **L2 `skill_library` API + L3 Open-Ideation의 H1b "non-knob structural patch"** 13 source 종합. K1-δ가 패러다임(Voyager) evidence라면 본 페이지는 **EDA 영역에서 reversible patch + structural transform의 구체 operator 도출**.

## Spec Direct Backing — 3-way 교집합 정의

> **L2.skill_library = "Voyager × SEVerA × RSR" 교집합** — executable skill + formal guard + Pareto reflection. `wiki/skills/` append-only 운용.

| 컴포넌트 | 출처 |
|----------|------|
| executable skill (file 저장 가능 transform) | Voyager (#1) |
| formal guard ("DRC clean + STA positive slack" 계약) | SEVerA (#7) |
| Pareto-driven reflection | Retrieve-Schedule-Reflect (#10) + EvolVE IGR (#8) |

## Spec H1b "non-knob structural patch" 정량화

L3 Open-Ideation은 **EvolVE IGR 계열 mutation을 "부록 C exclusion 미준수 시 자동 reject"하는 lint**로 감싸 H1b를 정량 지표화. 본 페이지에서 도출:

| structural transform 후보 | source | exclusion 여부 |
|---------------------------|--------|----------------|
| array-partitioning (정사각 → rectangular slab) | SISA #13 | **non-knob** ✓ |
| Idea-Guided Refinement (구조 변경 제안) | EvolVE #8 | non-knob (단, IGR 자체가 명시 분류는 아직 없음 — 본 프로젝트가 lint로 분류) |
| HW/SW co-design 재구성 | MACO CGRA #11 | **non-knob** ✓ (CGRA는 Gemmini보다 자유도 ↑, 본 프로젝트는 systolic 한정) |
| skill graph 재구성 (REFLECT 단계) | PSN #2 | meta-level (skill library structure) |
| meshRows / meshColumns knob 변경 | (Gemmini 부록 C.1) | **exclusion** ✗ — H1b 부적격 |

## Source 카테고리

### Voyager 계열 skill library (5종)
- **Voyager** (Wang NeurIPS 2023, foundational, critical-read): ever-growing executable skill 개념의 출발점. JS code append-only + self-verification 등록. **버전·롤백·patch DAG는 미구현** — η가 EDA 맥락에서 채울 빈자리.
- **PSN** (Shi 2026, recent-SOTA, critical-read): Voyager flat library를 Claude Opus 4.5로 offline-refactor하여 **7 generic + 20 wrapper + 38 unchanged** 계층 압축. **REFLECT structured fault localization** + **maturity-aware update gating** — L2 lint의 skill deprecation 정책 직접 참고.
- **SAGE** (Wang 2025, recent-SOTA): Sequential Rollout + Skill-integrated Reward (outcome reward 보완). 효과적 skill만 잔존. RL이 자연스럽게 skill pruning 수행 — reproducibility seed × 3 기준 설계 모델.
- **SEAgent** (2025, recent-SOTA): World State Model + Curriculum Generator + adversarial imitation(실패) + GRPO(성공). Voyager auto-curriculum의 최신 형태. OSWorld 5 신규 SW에서 11.3% → 34.5%.
- **EXIF** (Yang 2025): Explorer agent(Alice) + Target agent(Bob) 이중 loop. **Alice가 실패 리포트 보고 skill gap 메우기** 구조 — EDA에서 OpenROAD/Yosys `*.rpt` 입력 매핑.

### Skill governance / Survey (2종)
- **AgentSkills Survey** (Xu 2026, critical-read): skill을 "composable packages of instructions, code, resources" 공식화. 획득 3축(RL-with-skill / autonomous discovery / compositional synthesis). **26.1% 커뮤니티 skill에 vulnerability** + **graduated deployment permission 4-tier governance** — §7.2 blinded audit·signing 기준의 선행 사례.
- **SEVerA** (Banerjee 2026, recent-SOTA, critical-read): Planner LLM이 agent program 합성 + **Formally Guarded Generative Models**가 출력 계약 강제 (verified rejection sampling). **Reversible-patch에 formal guard를 붙이는 가장 최근 frame** — η skill 등록 시 "DRC clean + STA positive slack" 계약을 formal guard로 인코딩하는 설계 근거.

### EDA-specific multi-agent (3종)
- **Marco** (NVIDIA 2025, recent-SOTA): Layout 최적화 / Verilog·DRC coding / MCMM timing을 graph-based task-solving으로 통합. **MCMM timing agent 60× 가속, path debug 86%**. L1 Fargate Map 분할 + L2 skill DAG 산업 reference.
- **RSR** (Retrieve-Schedule-Reflect, Ouyang 2026): RAG로 expert 지식 search tree + Pareto-driven feedback + language reflection. **RL 대비 10% timing ↑, 4× 속도**. ORFS-agent 동류 — η는 "knob scheduling"을 넘어 **structural patch를 skill로 승격**하는 한 단계 위.
- **MACO** (Jiang 2025): CGRA H/W-S/W co-design 4단계 iterative + exponentially decaying exploration. **CGRA는 Gemmini보다 구조 자유도 ↑** — structural mutation이 H/W-S/W 공간을 함께 움직이는 사례.

### Mutation operator concrete (2종)
- **EvolVE** (Hsin 2026, recent-SOTA, critical-read): MCTS(기능 정확성) vs **Idea-Guided Refinement(최적화)** + Structured TB Generation. IC-RTL industry-scale에서 **66% PPA ↓**. **단 abstract 수준에서 "structural vs parametric mutation 구분 미명시"** — η가 IGR을 "non-knob patch"로 정제 + lint로 검증이 차별점.
- **SISA** (2026, recent-SOTA, mutation-operator): 정사각형 systolic을 **rectangular slab로 partitioning** + 작은/skewed matrix 독립 스케줄링. **8.52× 속도, 93% EDP ↓**. **Gemmini 부록 C.1 exclusion list(meshRows/Columns knob)를 벗어나는 structural patch operator의 구체 prior** — H1b 카탈로그 첫 entry 후보.

### RL-for-chip baseline (1종 + 2종 배경)
- **AlphaChip** (DeepMind 2024 addendum): pre-trained checkpoint 공개. TPU v5e 10 블록 −3.2% wirelength → Trillium 25 블록 −6.2%, MediaTek Dimensity Flagship 5G 확장. **RL이 chip placement에 patch-based 반복 개입의 기준선** — 단 η는 placement 아닌 **RTL 단계 structural transform** 겨냥 ([[k1-beta-agentic-eda-evidence]] False Dawn 논쟁 회피).
- 배경: Koza GP (1992) — HDL 진화의 개념적 선조 (rewrite-rule 회로 합성). η는 LLM-guided mutation이 GP structural operator에 수렴함을 전제.
- 배경: PIT/Mothra (SW mutation testing) — mutation → kill/survive 프레임이 L2 lint의 "skill acceptance gate"로 전이.

## 본 프로젝트와의 연결 (Direction Evidence)

### L2 skill_library API governance (3-tier 결정)

| 항목 | K2-η 도출 |
|------|-----------|
| skill 저장 형식 | Voyager append-only (executable code + frontmatter contract) |
| skill 등록 게이트 | reproducibility seed × 3 (SAGE) + blinded audit (AgentSkills 4-tier) + formal guard (SEVerA) |
| skill deprecation | PSN maturity-aware update gating (REFLECT 단계) |
| skill 카테고리 | RSR Pareto-driven feedback + EXIF gap-filling |
| skill DAG 운용 | Marco graph-based task-solving 참조 |

### 부록 C exclusion vs structural transform 정의 강화

본 페이지가 H1b "non-knob structural patch" 정의를 spec 부록 C와 보강:

- **exclusion (knob 변경)**: meshRows/meshColumns 등 Gemmini 탐색 공간의 parameter
- **non-knob (structural transform)**: array-partitioning(SISA), IGR 구조 제안(EvolVE), HW/SW co-design(MACO 정신, Gemmini 한정 적용)

### Spec §7.2 blinded audit + signing

AgentSkills survey의 **26.1% 취약점 + 4-tier permission governance**를 본 프로젝트 §7.2 blinded audit 기준에 직접 매핑. tier 정의:

| Permission tier | K2-η 매핑 |
|-----------------|-----------|
| Tier 1 (sandbox) | autonomous discovery skill — review 전 |
| Tier 2 (limited) | seed × 3 reproducibility 통과 |
| Tier 3 (broad) | blinded audit 통과 + formal guard 부착 |
| Tier 4 (admin) | (본 프로젝트 미사용) |

## Novelty surface (H1b 정량 지표화)

3개 source의 교집합이 본 프로젝트의 publishable seam:

1. **Karpathy-wiki ([[k1-delta-research-memory-evidence]])** — 지식 durability
2. **Voyager skill library (본 페이지 #1)** — executable memory
3. **EvolVE mutation ([[k1-alpha-llm-for-hdl-evidence]])** — structural transform

**삼자를 EDA `*.rpt` artifact로 엮으면**: 상용 PPA 경쟁이 아니라 **"재사용·역전 가능한 구조 transform 카탈로그"**라는 학술/프로세스 novelty 성립. spec §1 intent ("academic/process novelty vs commercial chips")의 구체 산출물.

## 미해결 / 추가 탐색

- **structural transform taxonomy 부재**: EvolVE IGR + SISA slab + MACO co-design을 **통일된 operator taxonomy**로 수집한 자료 없음 — 본 프로젝트가 1차 카탈로그 기여 가능.
- **skill DAG 운용 시 conflict 해소**: PSN REFLECT가 fault localization 제공하지만, 두 skill이 동일 path 충돌 시 어떤 우선순위로 적용할지 spec 미정.
- **formal guard 인코딩 방식**: SEVerA verified rejection sampling을 본 프로젝트 `.rpt` 계약으로 어떻게 변환할지 G2 직전 결정.
- **mutation reproducibility seed × 3 + blinded audit 비용**: AgentSkills 26.1% vulnerability 수치를 EDA에서는 어떤 ratio로 잡을지 — 실측 시점에 결정.

## 교차 참조

- [[k1-alpha-llm-for-hdl-evidence]] — EvolVE IGR mutation의 출처. H1b 정량 지표화 정합.
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent / RSR / Marco가 본 페이지 multi-agent reference의 prior layer (knob 수준).
- [[k1-delta-research-memory-evidence]] — Karpathy + Voyager 패러다임 evidence — 본 페이지가 EDA 영역으로 specialize.
- [[k1-gamma-opensource-eda-evidence]] — Marco의 60× MCMM 가속이 LibreLane 3.0.2 stack 위에서 어떻게 가능한지 (Tool plane 실증).
- [[k2-epsilon-graph-quality-judge-evidence]] — skill 등록 시 evaluator separation + Cohen's κ ≥ 0.6 적용 — AgentSkills 4-tier governance와 결합.
- [[k2-zeta-l1-runtime-evidence]] — Marco graph scheduler가 Step Functions Distributed Map과 정합. skill 실행이 L1 runtime 위에서.
- [[eda-flow-report-reading]] — `*.rpt` artifact가 skill formal guard의 input.
- [[fsm-and-pipeline]] — systolic의 array-partitioning(SISA) transform 단위.
- (pending) `[[k2-theta-benchmark-license-evidence]]` — 본 페이지 transform 카탈로그가 MLPerf Tiny v1.3 평가에서 검증.

## Source

- 원본: `raw/papers/k2-eta-patch-mutation.md` (2026-04-22 collected, 13 sources, confidence: medium → spec 채택 시 high)
- decision_anchors: `raw/imports_manifest.yaml`
- 직접 backing: `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` (skill_library) + `docs/superpowers/specs/2026-04-26-L3-content-design.md` (Open-Ideation mutation)
