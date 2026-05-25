---
type: raw-import
axis: mu
title: "K3 μ. VeriMaAS — multi-agent RTL workflow + EDA error feedback (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트 L2.memory.recall 디자인의 *directly comparable* 사례. error log를 agent reasoning에 dynamic 주입하여 workflow composition을 자동 갱신. Yosys + OpenSTA 통합. 본 프로젝트의 *project-wide wiki-first* 대비 *workflow-internal log-grounded*."
---

# μ. VeriMaAS — Automated Multi-Agent Workflows for RTL Design (positioning baseline)

## Meta

- **Scope**: multi-agent RTL workflow composition + formal verification feedback from HDL synthesis tools
- **본 K3 축 역할**: L2.memory.recall이 *workflow-internal error log-grounded ranking*과 어떻게 다른가 정량 비교. 두 시스템 모두 *agent decision에 EDA tool feedback 주입*이라는 핵심 메커니즘 공유, 차이는 *recall scope* (per-workflow vs project-wide cumulative)
- **Spec 참조**: L2 파생 spec §5.2 output schema (L2.memory.recall의 9 추가 field), overview spec §3.2 L2 contract table
- **K1+K2 cut-off (2026-04-22) 이후 발표** — 2025-09-24, K3 ingest 필수

## Primary Source

### 1. VeriMaAS — Automated Multi-Agent Workflows for RTL Design (2025-09-24)
- arXiv: https://arxiv.org/abs/2509.20182 / https://arxiv.org/html/2509.20182v1
- OpenReview: https://openreview.net/pdf?id=S4Fqovim3F
- GitHub (WiP, documentation-migration in progress): https://github.com/dstamoulis/maas/tree/verimaas/verithoughts
- Tag: [recent-SOTA, comparative-baseline, multi-agent, open-source]
- WHAT: Multi-agent framework that **adaptively samples reasoning operators** per RTL task. 각 step에서 candidate Verilog 디자인이 **Yosys + OpenSTA** synthesis/verification pipeline에 실행되고, error log가 다음 operator selection에 dynamic feedback. **5-7% pass@k 개선** over fine-tuned baselines, **few hundred training examples만 필요** (fine-tuning 대비 supervision cost 10x 감축). VerilogEval + VeriThoughts 두 벤치마크에서 입증.
- WHY: 본 프로젝트 L2.memory.recall이 *EDA tool feedback (`.rpt` outputs)을 agent reasoning에 주입*하는 메커니즘과 *직접 비교 가능*. 다만 VeriMaAS는 **per-workflow transient** (단일 task 내), 본 프로젝트는 **project-wide cumulative** (iteration 간 누적).

## 본 프로젝트와의 5축 비교

| 차원 | VeriMaAS (2025-09) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | 없음 (technical demo) | INTENT.md cycle + Learnings 진화 | **본 프로젝트만** 메타 layer |
| **(b) Context routing** | **workflow-internal log-grounded operator ranking** (per-task) | **project-wide wiki-first hybrid** (cumulative) | scope 차이 — VeriMaAS는 *running workflow 내*, 본 프로젝트는 *project lifetime 전체* |
| **(c) Agent 분업** | adaptive operator sampling (PPO-style transient roles) | 4 fixed roles + Operator authority | **dynamic vs static** — VeriMaAS는 role을 *task별 sampling*, 본 프로젝트는 *고정 분업* |
| **(d) Scientific contribution** | pass@k metric improvement (5-7%) | reasoning trace κ ≥ 0.6 + H1b 3건 | **다른 contribution 축** — VeriMaAS는 *accuracy*, 본 프로젝트는 *process fidelity + novelty count* |
| **(e) Skill accumulation** | workflow composition (transient, per-run discarded) | reversible-patch skill library (persistent, iteration-grow) | **transient vs persistent** — 본 프로젝트만 누적 |

**핵심 차이 (recall scope)**: VeriMaAS의 *workflow-internal log-grounded ranking*은 본 프로젝트 L2.memory.recall이 추구하는 *project-wide cumulative*의 *subset 사례*. 즉 VeriMaAS는 L2.memory.recall의 *축소판*(per-workflow scope)이라 본 프로젝트가 *superset 메커니즘 설계 가능*. L2 파생 spec §5.3 ranking calibration weight (α tier 0.30 / β confidence 0.30 / γ freshness 0.20 / δ centrality 0.20)는 VeriMaAS의 *transient operator selection*과 *호환 가능*하되, *cross-workflow persistence*가 본 프로젝트 차별화.

## K1/K2 cross-link 후보

- **K2-ε** `k2-epsilon-graph-quality-judge-evidence` — VeriMaAS의 *workflow-internal log-grounded ranking*과 본 프로젝트 confidence tier 매핑(GOLD/SILVER/BRONZE) 비교. *workflow-transient*에서 *project-cumulative*로 확장 시 ranking weight 재calibration 필요 여부 검토
- **K2-η** `k2-eta-patch-mutation-evidence` — VeriMaAS의 *adaptive operator sampling*이 본 프로젝트 reversible-patch와 *형식적으로 호환되는가* 분석 (operator = patch unit으로 해석 가능 여부)

## 본 K3 evidence의 spec/INTENT 영향

- **L2 파생 spec §3.2 alternative B** 검토 시 VeriMaAS의 *workflow-internal log-grounded* 패턴을 *project-wide cumulative*로 확장하는 design choice를 명시 후보. 현재 L2 파생 spec은 confidence/freshness 정의는 명시되어 있으나 *cross-workflow vs intra-workflow* scope 구분 부재.
- **INTENT.md Why > 문제 두 번째 bullet** 이미 인용 완료 (commit `4148ff5`, 2026-05-25) — VeriMaAS가 6 인접 작업 중 하나로 list.
- **INTENT.md What > 핵심 기능 > L2 Substrate** 갱신 완료 (2026-05-25) — VeriMaAS *workflow-internal* 대비 *project-wide wiki-first hybrid* 차별화 명시.

## Pending (Operator 결정)

- [ ] GitHub repo(`dstamoulis/maas`) 활성 여부 + 라이선스 verify — "WiP, documentation-migration in progress" 명시
- [ ] VeriMaAS의 *operator sampling*이 본 프로젝트 agent system prompt와 *형식 비교 가능*한지 분석 (Verilog operator vs LLM agent prompt의 일치 정도)
- [ ] L2 파생 spec §5.3 ranking weight 4축(α/β/γ/δ)이 VeriMaAS *transient operator selection*과 *cross-workflow extension* 결합 시 안정성 검증
