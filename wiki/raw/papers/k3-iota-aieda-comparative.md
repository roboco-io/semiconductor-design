---
type: raw-import
axis: iota
title: "K3 ι. AiEDA — concept-to-GDSII 4-stage agentic flow (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트와 *scope에서 가장 유사*한 인접 작업. concept(architecture) → RTL → synthesis → physical 4 stage agentic flow + sky130A 채택 + RAG Verilog gen. INTENT/wiki/Operator/role-split/reasoning-trace 5 차원 비교로 본 프로젝트의 *true novelty boundary* 정량화. 본 K3 축은 K1(forward synthesis)/K2(backward spec backing)와 달리 *competitive positioning evidence*에 한정."
---

# ι. AiEDA — Agentic AI Design Framework for Digital ASIC (positioning baseline)

## Meta

- **Scope**: Open-Ideation DSE를 *agentic flow* 단위로 시도한 사례. 본 프로젝트와 가장 가까운 *scope* (full concept-to-GDSII + open-source EDA + sky130A).
- **본 K3 축 역할**: "본 프로젝트의 차별화 축 (a) 의도공학 layer / (b) wiki-first hybrid routing / (c) 4-role + Operator authority / (d) reasoning trace as primary contribution / (e) reversible-patch skill library" 5 차원을 AiEDA 대비 정량 비교.
- **Spec 참조**: overview spec §3 architecture (3-layer 정합 확인), §5.3 canonical decision table (어느 차원이 publish/kill 분기에 영향), INTENT.md What §4 (5 layer 완전 결합 사례 존재 여부).
- **K1+K2 cut-off (2026-04-22) 이후 발견 아님** — AiEDA는 2024-08-29 발표, K1+K2가 *miss*한 작업. K3는 K1/K2의 차별화 검증 보강.

## Primary Source

### 1. AiEDA: Agentic AI Design Framework for Digital ASIC System Design (2024-08-29)
- URL: https://ar5iv.labs.arxiv.org/html/2412.09745
- Tag: [foundational, critical-read, comparative-baseline]
- WHAT: Concept-to-GDSII 4-stage agentic flow — (1) Architecture (Python), (2) RTL (LLM + RAG Verilog), (3) Netlist synthesis, (4) Physical design. 각 stage가 LLM + 적절한 EDA tool feedback loop. **Sky130 standard cell + PDK 채택** (본 프로젝트와 동일). 핵심 기법: prompt engineering, few-shot learning, self-reflection, RAG.
- WHY: 본 프로젝트의 *full agentic flow* 비전과 직접 비교 가능한 *유일한 single-paper baseline*. 다만 *single paper, sustained program 아님*이라 본 프로젝트의 *AutoResearch* 포지셔닝과 직교.

## 본 프로젝트와의 5축 비교

| 차원 | AiEDA (2024) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | 없음 (기술적 보고서) | INTENT.md 의도공학 + Operator·project co-evolution | **본 프로젝트만** Why/What/Not/Learnings 4-section meta-doc |
| **(b) Context routing** | RAG (Verilog code data, retrieval-augmented generation) | Karpathy wiki-first hybrid + graphify 보조 | **다른 routing 패러다임** — AiEDA는 *문맥 보강*, 본 프로젝트는 *컴파일된 위키 참조* |
| **(c) Agent 분업** | 단일 LLM이 각 stage 담당, *role split 없음* | 4-role (designer/runner/code-author/eda-reviewer) + Operator | **본 프로젝트만** role-explicit 분업 + Operator authority |
| **(d) Scientific contribution** | "agentic design 실증" (technical demo) | reasoning trace H3 Cohen's κ ≥ 0.6 | **다른 contribution 축** — AiEDA는 *기능 시연*, 본 프로젝트는 *프로세스 신뢰성 측정* |
| **(e) Skill accumulation** | 단일 run 내 self-reflection만, 누적 없음 | reversible-patch skill library (Voyager × EDA) | **본 프로젝트만** 명시적 patch 누적 메커니즘 |

**중첩 차원**: sky130A 채택, multi-stage agentic, open-source EDA. → 본 프로젝트가 AiEDA의 *기술 substrate*은 공유, *메타 layer + 운영 모델 + scientific framing*에서 분기.

## K1/K2 cross-link 후보

- **K1-β** `k1-beta-agentic-eda-evidence` — ORFS-agent 비교에 *AiEDA도 함께* 비교 항목으로 추가 (parameter tuning ORFS-agent vs full-flow AiEDA vs structural patch 본 프로젝트의 3축 구도)
- **K1-α** `k1-alpha-llm-for-hdl-evidence` — RAG-based Verilog generation을 LLM-for-HDL 도구 카탈로그에 보강
- **K2-η** `k2-eta-patch-mutation-evidence` — H1b structural transform 첫 entry(SISA array-partitioning)와 AiEDA의 *self-reflection 부재*를 대비. 본 프로젝트만 reversible-patch 누적

## 본 K3 evidence의 spec/INTENT 영향

- **INTENT.md Why §11** 갱신 후보: "기존 agentic EDA (ORFS-agent 2025)는 parameter knob tuning에 한정" → **"AiEDA(2024)·CHIPCRAFTBRAIN(2026)·VeriMaAS(2025) 등 multi-agent agentic flow 시도도 의도공학 + wiki-first + Operator authority + reasoning trace + reversible-patch 5축 동시 결합 사례 없음"**
- **본 K3 페이지는 *컴파일 대상 아님*** — wiki/{slug}.md 페이지로 격상은 K1/K2 evidence와 cross-link 이후 별도 결정 (skim-and-defer 권장)

## Pending (Operator 결정)

- [ ] AiEDA GitHub repo 존재 여부 verify (URL에 미명시) — `perplexity_search "AiEDA GitHub 2024 sky130"` 후속
- [ ] AiEDA의 평가 metric(reasoning trace 측정 부재 vs 본 프로젝트 H3 κ)을 spec §5.3 R0 invariant에 영향 여부 검토
- [ ] 본 K3 evidence가 INTENT.md Why §11 *수정 필수*인지 *참조 부속*인지 판정
