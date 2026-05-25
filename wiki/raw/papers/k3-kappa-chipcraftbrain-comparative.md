---
type: raw-import
axis: kappa
title: "K3 κ. CHIPCRAFTBRAIN — 6-agent + PPO orchestration (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트와 *agent role split에서 가장 유사*한 인접 작업. 6개 specialized agents + PPO 정책 + hybrid symbolic-neural + 321 패턴 + 971 reference impls. 본 프로젝트의 4-role + Operator authority와 *철학적 정반대* (autonomous coordination vs human-in-loop). 비교 baseline으로 강력."
---

# κ. CHIPCRAFTBRAIN — Validation-First RTL Generation via Multi-Agent Orchestration (positioning baseline)

## Meta

- **Scope**: Multi-agent system for automated RTL generation. *agent role split*과 *orchestration mechanism*에서 본 프로젝트와 직접 비교 가능.
- **본 K3 축 역할**: 본 프로젝트의 *Operator authority* 모델이 *autonomous PPO-orchestrated* 모델 대비 어떤 차별을 가지는지 정량 비교. agent coordination의 두 패러다임 직접 대비.
- **Spec 참조**: overview spec §7 operating rules (Operator 결정 권한), §5.3 canonical decision table R0~R6, INTENT.md Not §61 ("Researcher/Developer 역할 사람 추가 금지" — single-operator multi-agent 구조 유지).
- **K1+K2 cut-off (2026-04-22) 이후 발표** — 2026-04, K3 ingest 필수 대상.

## Primary Source

### 1. CHIPCRAFTBRAIN: Validation-First RTL Generation via Multi-Agent Orchestration (2026-04)
- URL: https://arxiv.org/pdf/2604.19856.pdf
- Tag: [recent-SOTA, critical-read, comparative-baseline, multi-agent]
- WHAT: 6 specialized LLM agents (4개 RL-orchestrated + 2개 rule-based)을 168-dim 상태 위 PPO 정책으로 coordinate. 추가로: hybrid symbolic-neural (K-map/truth table은 algorithmic 0-cost), knowledge-augmented generation (321 도메인 패턴 + 971 reference implementations + focus-aware retrieval), hierarchical specification decomposition. **Sky130 PDK + RTL-to-GDSII 채택**.
- WHY: 본 프로젝트의 *4-role + Operator* 모델과 *6-agent + PPO* 모델이 *동일 문제 공간*을 *정반대 철학*으로 푼다 — 본 프로젝트 = human-in-loop authority, CHIPCRAFTBRAIN = autonomous coordination. 양 모델의 *trade-off 차원* 비교 자료.

## 본 프로젝트와의 5축 비교

| 차원 | CHIPCRAFTBRAIN (2026-04) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | 321-패턴 knowledge base (정적) | INTENT.md (의도공학 진화 layer) | **정적 vs 진화** — KB는 미리 큐레이션, INTENT.md는 Learnings로 cycle 진화 |
| **(b) Context routing** | focus-aware retrieval (321 패턴 + 971 ref impls) | Karpathy wiki-first hybrid | **다른 패턴 — CHIPCRAFTBRAIN은 *임베디드 패턴 매칭*, 본 프로젝트는 *컴파일된 위키*** |
| **(c) Agent 분업** | **6 agent (4 RL + 2 rule)** | **4 agent (designer/runner/code-author/eda-reviewer)** + Operator | **agent count 유사, 권한 모델 정반대** — PPO autonomous vs Operator authority |
| **(d) Scientific contribution** | hybrid symbolic-neural의 *zero-cost K-map/truth table* (구체 metric) | reasoning trace H3 κ ≥ 0.6 | **다른 contribution 축** — CCB는 *기법 신규성*, 본 프로젝트는 *프로세스 신뢰성* |
| **(e) Skill accumulation** | 971 reference impls 정적 보유 | reversible-patch skill library 누적 | **정적 vs 누적** — CCB는 *고정 카탈로그*, 본 프로젝트는 *iteration-grow* |

**철학적 차이**: CHIPCRAFTBRAIN은 *agent coordination을 RL 정책으로 자동화* — Operator 부재. 본 프로젝트는 *agent coordination을 human authority로 명시* — INTENT.md Not §61 "Researcher/Developer 역할 사람 추가 금지"가 이 boundary 보장. 본 차이가 H3 가설(reasoning trace 복원 가능성)에 핵심 — autonomous coordination은 *decision provenance*가 흐려지기 쉬움.

## K1/K2 cross-link 후보

- **K1-β** `k1-beta-agentic-eda-evidence` — ORFS-agent (parameter tuning) + AiEDA (full flow, single LLM) + CHIPCRAFTBRAIN (multi-agent + RL) + 본 프로젝트 (multi-agent + Operator)의 4축 grid 추가
- **K2-η** `k2-eta-patch-mutation-evidence` — CCB의 *971 ref impls*는 reversible-patch skill library의 *정적 baseline* 비교 자료. H1b non-knob 정의 vs CCB의 "여기 있는 패턴 재사용"의 차이 명시 필요
- **K2-ε** `k2-epsilon-graph-quality-judge-evidence` — CCB가 *evaluation judge 없음* (자동 PPO 보상)을 본 프로젝트의 LLM-as-judge κ ≥ 0.6 falsifier와 대비

## 본 K3 evidence의 spec/INTENT 영향

- **INTENT.md Why > 문제 두 번째 bullet 갱신 ✅** (commit `4148ff5`, 2026-05-25) — 본 raw의 trigger가 직접 반영. 5축 framing 채택. ⚠ 직전 wording "§11"은 self-fabrication (INTENT.md numbered section 부재), Operating Invariant #4 적용 사례.
- **spec §7 operating rules** 보강 후보: "agent autonomy boundary" 명시 — CHIPCRAFTBRAIN-style PPO 자동화의 *trade-off* (속도 ↑, decision provenance ↓)를 INTENT.md 메타 목적 (의도공학 layer)과 대비
- **H3 가설 강화**: CCB의 *evaluator-less autonomous coordination*이 본 프로젝트 H3 "Cohen's κ ≥ 0.6 + evaluator separation rule"의 *대조군 baseline*으로 기능 — 즉 본 프로젝트 H3 falsifier가 CCB-style 시스템의 *blind spot*을 직접 노출

## Pending (Operator 결정)

- [ ] CHIPCRAFTBRAIN GitHub repo / 오픈소스 여부 verify — 논문에 미명시
- [ ] 168-dim 상태 표현의 *어떤 차원*이 본 프로젝트의 reasoning trace schema와 매핑되는지 분석
- [ ] CCB의 971 ref impls *내용*이 본 프로젝트 reversible-patch와 *형식적 비교 가능*한지 (실제 patch unit 정의 비교)
- [ ] 본 K3 evidence가 INTENT.md *Not* 섹션 보강 trigger인지 (예: "PPO autonomous coordination 채택 금지" 명시)
