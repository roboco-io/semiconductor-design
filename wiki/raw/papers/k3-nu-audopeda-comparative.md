---
type: raw-import
axis: nu
title: "K3 ν. AuDoPEDA — repository-grounded EDA tool code modification (positioning evidence)"
date: 2026-05-25
phase: K3
curator: claude-opus-4-7
source_count: 1
intent: "본 프로젝트와 *다른 layer*에서 작동하는 인접 작업 — RTL/constraint patch 대신 *EDA tool source code 직접 수정*. WL 5.9% / clock 10% 개선. 본 프로젝트와 *complementary* (수직 분리, 충돌 아님)."
---

# ν. AuDoPEDA — Autonomous Documentation and Planning for EDA (positioning baseline)

## Meta

- **Scope**: agentic coding system that modifies *EDA tool source code* (OpenROAD repo) — RTL/constraint design layer가 아닌 *도구 자체 개선*
- **본 K3 축 역할**: 본 프로젝트와 *수직 분리* 사례 — 두 시스템이 stack의 다른 층에서 작동. competitive가 아닌 **complementary** 관계 정리
- **Spec 참조**: INTENT.md Not 절대 금지 #5 ("`wiki/raw/` 원본 수정 금지" — 본 프로젝트의 reversible patch 정신) 대조, overview spec §7 reversible-patch 원칙
- **K1+K2 cut-off (2026-04-22) 이후 발표** — 2026-01, K3 ingest 필수

## Primary Source

### 1. AuDoPEDA — Automated QoR improvement in OpenROAD with coding agents (2026-01)
- arXiv: https://arxiv.org/pdf/2601.06268v1.pdf
- Tag: [recent-SOTA, comparative-baseline, code-mod-layer, complementary]
- WHAT: **Codex-class executor** + **DSPy planner** + **graph-based code documentation**. OpenROAD repo 전체를 자동 indexing → research direction 제안 → implementation step expansion → **executable diff** OpenROAD source에 submit → compile/run/hill-climb against PPA targets. WL 5.9%, clock period 10.0% 개선 (fixed benchmark + acceptance test). **end-to-end EDA codebase modification 첫 입증 시스템** ("first Autonomous Documentation and Planning system for EDA codebases").
- WHY: 본 프로젝트가 *RTL/constraint 설계 layer*에서 작동한다면 AuDoPEDA는 *EDA tool source layer*에서 작동. 두 layer가 *동시 협력 가능* — AuDoPEDA가 도구를 개선하고 그 도구를 본 프로젝트가 사용. 본 프로젝트의 K1+K2 evidence에서 *완전히 missed*된 layer.

## 본 프로젝트와의 5축 비교

| 차원 | AuDoPEDA (2026-01) | 본 프로젝트 | 차이 |
|---|---|---|---|
| **(a) 메타 layer** | 없음 (technical demo) | INTENT.md + Learnings 진화 | **본 프로젝트만** 메타 layer |
| **(b) Context routing** | repository-grounded (DSPy + graph documentation, code-level) | wiki-first hybrid (knowledge-level) | **다른 substrate** — AuDoPEDA는 *code AST graph*, 본 프로젝트는 *knowledge wiki graph* |
| **(c) Agent 분업** | Codex-class executor + DSPy planner (2-tier) | 4-role + Operator (5-tier) | layer 다른 분업 |
| **(d) Scientific contribution** | PPA improvement on fixed benchmark (WL 5.9%, clock 10%) | reasoning trace fidelity + structural patch novelty | **다른 contribution 축** — AuDoPEDA는 *tool QoR*, 본 프로젝트는 *design process* |
| **(e) Skill accumulation** | accepted patches (OpenROAD source mainline merge) | reversible RTL/constraint patches (skill library) | **layer + persistence 모두 다름** |

**핵심 차이 (*수직 분리*)**: AuDoPEDA는 *EDA tool source* layer 수정 (개발자가 OpenROAD에 patch 제출), 본 프로젝트는 *RTL/constraint design* layer 수정 (디자이너가 chip RTL에 patch). 두 시스템이 *동시 협력 가능*. **competitive가 아닌 complementary**.

**INTENT.md Not 정합 검증**:
- Not 절대금지 #5 "`wiki/raw/` 원본 수정" 위반 아님 — AuDoPEDA는 *EDA tool source*만 수정, *본 프로젝트의 wiki/raw 영역* 미관여
- overview spec §7 reversible-patch 원칙 비교: AuDoPEDA는 *baseline 직접 수정* (mainline merge), 본 프로젝트는 *patch unit 보존 + reversible*. **다른 layer라 reversible 원칙 위반 아님** — AuDoPEDA의 baseline은 OpenROAD repo이고 본 프로젝트의 baseline은 chip RTL design.

## K1/K2 cross-link 후보

- **K2-η** `k2-eta-patch-mutation-evidence` — reversible-patch 정의에 *layer 명시* 추가 필요 ("RTL/constraint level — EDA tool source 수정은 *별 layer*이고, AuDoPEDA-style code mod은 본 프로젝트 reversible patch 정의 *범위 밖*")
- **K1-γ** `k1-gamma-opensource-eda-evidence` — OpenROAD 발전 trajectory에 AuDoPEDA-style autonomous code modification이 *외부 contribution 메커니즘* 추가됨을 명시
- **K3-λ** `k3-lambda-ucsd-abk-program-comparative` — AuDoPEDA가 UCSD ABK lab 작업인지 verify 필요. ABK라면 λ에 통합, 별도면 ν 분리 유지

## 본 K3 evidence의 spec/INTENT 영향

- **INTENT.md Why > 문제 두 번째 bullet** 이미 인용 완료 (commit `4148ff5`, 2026-05-25) — AuDoPEDA가 6 인접 작업 중 하나로 list. complementary 관계 명시.
- **본 프로젝트 lockfile.yaml SHA-pin 정책 영향**: AuDoPEDA-style tool source 수정이 *upstream에 merge*되면 lockfile SHA가 변경 → 본 프로젝트는 *SHA freeze*로 보호. 즉 본 프로젝트 KG-A (toolchain reproducibility)가 AuDoPEDA-style *upstream churn*에 robust한지 KG-A pass criteria로 입증 가능 (KG-A의 *부가 가치*).

## Pending (Operator 결정)

- [ ] AuDoPEDA 저자 lab 확인 (UCSD ABK인지 verify — λ와 통합 결정)
- [ ] 본 프로젝트 lockfile.yaml SHA-pin이 AuDoPEDA-style upstream code mod에 robust함을 *KG-A pass 입증*에 명시 가능 여부
- [ ] L1 파생 spec §6.2 lockfile 정책에 "upstream churn (AuDoPEDA-style autonomous code mod 포함) robustness"를 invariant로 추가 후보
- [ ] complementary 관계 명시 — 본 프로젝트가 AuDoPEDA의 *결과 (개선된 OpenROAD)*를 사용 가능. 단 SHA freeze로 *upstream merge timing 통제* 필요
