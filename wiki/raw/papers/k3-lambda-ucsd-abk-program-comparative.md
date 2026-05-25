---
type: raw-import
axis: lambda
title: "K3 λ. UCSD ABK lab — sustained agentic EDA program (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트와 *sustained program 차원에서 가장 유사*한 인접 작업. UCSD ABK lab(Andrew B. Kahng 교수)이 ORFS-agent (2025-06)에서 ICCAD invited paper '*Agentic AI for Physical Design R&D: Status and Prospects*'로 확장 — flow/code/meta-agent 3-tier 비전 + multi-agent collaboration roadmap 제시. 본 프로젝트와 *비전 가장 유사한 sustained program* 이면서 *publishing positioning에서 직접 경쟁 관계*."
---

# λ. UCSD ABK Lab — Agentic AI for Physical Design R&D (sustained program baseline)

## Meta

- **Scope**: ORFS-agent (single paper)에서 ICCAD invited paper(position)로 확장한 *sustained agentic EDA research program*. UCSD ABK lab(VLSI-CAD 그룹, Andrew B. Kahng) 주도.
- **본 K3 축 역할**: 본 프로젝트의 *sustained AutoResearch program* 포지셔닝이 *기존 학계 program*과 어떻게 차별화되는가 정량 비교. 비교 대상이 *isolated paper*가 아닌 *multi-year initiative*인 첫 사례.
- **Spec 참조**: INTENT.md 메타 목적 #1 (의도공학 우수성 증명 사례 연구), #2 (Operator·project co-evolution publishing). overview spec §5.3 R0~R6 decision table의 publish vs reframed-publish vs kill 분기.
- **K1+K2 cut-off (2026-04-22) 이후 발표** — 2025-09 ICCAD, K3 ingest 필수.

## Primary Source

### 1. Agentic AI for Physical Design R&D: Status and Prospects (ICCAD 2025 invited)
- URL: https://vlsicad.ucsd.edu/Publications/Conferences/423/c423.pdf
- Tag: [recent-SOTA, critical-read, comparative-baseline, sustained-program]
- WHAT: UCSD ABK lab(Andrew B. Kahng)이 ICCAD 2025 invited talk으로 발표한 *position paper*. ORFS-agent (parameter tuning autotuner)에서 한 단계 위 — *agentic AI system for physical design*을 (i) interpret natural-language spec, (ii) invoke EDA tools + analyze outputs, (iii) modify tool configurations or source code, (iv) iteratively refine based on measured QoR — 4축으로 정의. **3-tier agent 구조 제시**: flow-level agents (configuration space exploration), code-level agents (HDL/script/EDA source 수정), meta-agents (progress monitoring, stagnation detection, compute allocation).
- WHY: 본 프로젝트의 *3-layer (L1/L2/L3)* + *4-role agent* 모델과 직접 비교 가능. 다만 UCSD ABK는 *autonomous coordination* 지향, 본 프로젝트는 *human-in-loop Operator authority* 명시 — 동일 *publishing 공간 (DAC/ICCAD/MLCAD)* 에서 분기.

## 본 프로젝트와의 5축 비교

| 차원 | UCSD ABK program (2025-09) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | position paper에서 *roadmap* 제시 (의도 layer 명시 아님) | INTENT.md 의도공학 + Learnings 진화 | **본 프로젝트만** 운영 중 진화하는 의도 layer |
| **(b) Context routing** | 미명시 (개별 agent별 자유) | Karpathy wiki-first hybrid (벤치 토큰 −53.6%) | **본 프로젝트만** 컨텍스트 substrate 결정 |
| **(c) Agent 분업** | flow/code/meta-agent 3-tier (autonomous) | designer/runner/code-author/eda-reviewer 4-role + **Operator authority 명시** | **3-tier vs 4-role**, autonomous vs Operator-supervised |
| **(d) Scientific contribution** | "agentic AI가 R&D loop에 end-to-end 참여 가능"이 핵심 주장 (capability claim) | **H3 reasoning trace κ ≥ 0.6** + reversible-patch H1b 3건 (measurable claim) | **capability vs measurement** — ABK는 *가능성*, 본 프로젝트는 *정량 falsifier* |
| **(e) Skill accumulation** | code-level agent의 *EDA tool source 수정*이 skill 후보로 함의 | reversible-patch skill library (Voyager × EDA), seed×3 재현 필수 | **다른 layer** — ABK는 *tool source*, 본 프로젝트는 *RTL/constraint patch* |

**핵심 차이 (publishing positioning)**: UCSD ABK는 *capability 시연*("LLM agent가 chip design R&D에 참여할 수 있다") 축, 본 프로젝트는 *measurable falsifier*("의도공학 + co-evolution 모델이 reasoning trace κ ≥ 0.6 + non-knob patch 3건을 *재현 가능하게* 산출한다") 축. 본 프로젝트의 §5.3 canonical decision table(R0-R6 + H3 R0 override)이 *publication kill criteria*로 작동 — ABK position paper에 이런 falsifier 부재.

**Sustained program 비교**:
- UCSD ABK: ORFS-agent (2025-06) → ORFS-agent v2/v3 (2025-09~2026-Q1) → ICCAD invited (2025-09) → AuDoPEDA (2026-01, 추정 같은 lab line) → 후속 ICCAD/DAC 예상. **3년+ sustained**.
- 본 프로젝트: 2026-04-17 시작, 2026-05-10 G1 첫 smoke plan freeze. **6주 진행, 본 K3 시점부터 sustained 형성**. UCSD ABK 대비 *훨씬 후발*이며, *차별화 축 명확화*가 publication path 핵심.

## K1/K2 cross-link 후보

- **K1-β** `k1-beta-agentic-eda-evidence` — ORFS-agent를 UCSD ABK program의 *첫 마일스톤*으로 재맥락. ABK program의 trajectory (single autotuner → 3-tier autonomous vision)와 본 프로젝트의 INTENT/wiki/Operator 5-axis 분기점을 명시
- **K2-ζ** `k2-zeta-l1-runtime-evidence` — ABK position paper의 *flow-level agent*가 본 프로젝트 L1.run(spec_uri) 인터페이스의 *대응물*. 두 인터페이스 contract 비교 필요
- **K2-ε** `k2-epsilon-graph-quality-judge-evidence` — ABK는 *evaluator/judge 메커니즘 미명시*. 본 프로젝트 H3 LLM-as-judge κ ≥ 0.6 falsifier가 *direct differentiator*

## 본 K3 evidence의 spec/INTENT 영향

- **INTENT.md Why §11** 핵심 갱신 trigger: "기존 agentic EDA는 parameter knob tuning에 한정"을 **"UCSD ABK가 ORFS-agent → ICCAD invited (3-tier autonomous vision)으로 program 확장 중. 본 프로젝트는 *동일 publishing 공간*에서 *human-in-loop Operator authority + measurable falsifier + reasoning trace*라는 3개 직교 축으로 분기"** 로 갱신 필수
- **INTENT.md What §4 (5 layer)** 갱신 후보: 5 layer 각각에 "UCSD ABK 대비 차별화" 1줄 추가 — 본 프로젝트의 *각 layer 결정*이 ABK roadmap과 어떻게 다른지 명시
- **spec §5.3 canonical decision table** 갱신 *불필요* — Learnings #1 invariant (INTENT.md/plan은 spec 재정의 금지). 본 K3는 INTENT.md positioning만 영향
- **publishing strategy 갱신 후보** (별도 문서): DAC/ICCAD/MLCAD 어느 venue가 본 프로젝트의 5축 차별화를 *evaluate 가능*한가 분석

## Pending (Operator 결정)

- [ ] ABK lab 후속 작업 추적 — 2026 Q2/Q3 발표 모니터링 ([VLSI-CAD UCSD publications](https://vlsicad.ucsd.edu/Publications/))
- [ ] AuDoPEDA (2026-01)가 정말 ABK lab 작업인지 verify (저자 명단 확인) — 본 K3-λ vs K3 별도 axis 분리 결정
- [ ] 본 K3-λ를 *INTENT.md Why 직접 갱신*에 반영할지, 별도 *publishing strategy doc*으로 분리할지 결정
- [ ] ABK ICCAD invited paper의 3-tier (flow/code/meta) agent와 본 프로젝트 4-role agent의 *역할 매핑 표* 작성 (별도 wiki/agent-role-comparison.md 후보)
