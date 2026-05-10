---
title: "K2-ε: Graph Quality + LLM-as-Judge + Human Triage — Direction Evidence"
type: synthesis
tags: [k2, graph-quality, llm-as-judge, cohen-kappa, graphrag, confidence-tier, freshness]
status: active
confidence: medium
created: 2026-05-10
updated: 2026-05-10
sources:
  - raw/papers/k2-epsilon-graph-quality-judge.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §3.2 L2 contract · §5.3 H3 falsifier
  - docs/superpowers/specs/2026-04-23-L2-substrate-design.md  # 본 evidence가 직접 backing
  - docs/superpowers/specs/2026-04-22-graphify-adoption-design.md  # AMBIGUOUS triage
---

# K2-ε: Graph Quality + LLM-as-Judge + Human Triage — Direction Evidence

본 프로젝트의 **L2 substrate spec**의 4 deferred items(per-node freshness · confidence_score 산식 · ranking calibration · `L2.memory.recall` query semantics) + **§5.3 H3 falsifier**(judge separation, Cohen's κ 문턱)의 21 source 종합. K1-δ가 패러다임 evidence라면 본 페이지는 **L2 산식·문턱·rule의 직접 backing**.

## Meta-Framing — spec deferred items와의 매핑

| spec deferred item | 본 페이지의 직접 evidence |
|--------------------|---------------------------|
| D-1 per-node freshness | Zep validity period · A-MEM memory evolution · LightRAG incremental update |
| D-2 confidence_score 산식 | Ahmed 2026 GOLD/SILVER/BRONZE + 0.95/0.85/0.70 fixed values |
| D-3 ranking calibration (graphify BFS/DFS budget × tier weight) | nano-graphrag tunable knobs · GraphRAG-Bench structural metrics |
| D-4 `L2.memory.recall` query semantics | Microsoft GraphRAG community-based retrieval + LightRAG dual-level |
| §5.3 H3 falsifier judge N≥5 + Cohen's κ ≥ 0.6 | Verga 2024 PoLL · Han 2025 Judge's Verdict · Landis-Koch 1977 + McHugh 2012 |
| FM1~FM4 rubric | Huang 2024 hallucination taxonomy (factuality vs faithfulness × 3 sub) |

## Source 카테고리

### Graph quality / GraphRAG (5종)
- **Microsoft GraphRAG** (Edge 2024, foundational): LLM entity·relation 추출 + Leiden community detection + 계층 community summary 사전 생성. graphify 상위 디자인 reference. 추출 품질 60-85%가 confidence baseline.
- **LightRAG** (Guo EMNLP 2025, recent-SOTA): dual-level retrieval + **incremental update** — 새 문서 ingest 시 전체 재색인 없이 그래프 갱신. **per-node freshness 메커니즘의 직접 모델**.
- **nano-graphrag** (gusye1234, ~800-line 재구현): `global_max_consider_community` 등 tunable knob 명시 노출. ranking calibration의 production reference.
- **safishamsi/graphify** (본 프로젝트가 채택): EXTRACTED / INFERRED(score) / AMBIGUOUS(review) 3-tier provenance. §7.3 AMBIGUOUS triage upstream.
- **GraphRAG-Bench** (2025, recent-SOTA): node count / non-isolated ratio 같은 **structure-based metric** 정식화. graphify M3 lint 기준의 외부 정렬 근거.

### Confidence tier / Provenance (1종 + 1종)
- **Ahmed 2026** (Clinical AI, critical-read): **GOLD/SILVER/BRONZE = 0.95/0.85/0.70 fixed** + cross-tier confirmed/multi-model consensus/single-source 정의. **본 프로젝트 confidence_score 재도입의 직접 템플릿**.
- **Snorkel** (Ratner VLDB 2017, foundational): ground truth 없이 noisy labeling function denoise. AMBIGUOUS 판정 후 human triage 직전 label model 단계 근거.

### Freshness / Memory evolution (2종)
- **Zep / Graphiti** (Rasmussen 2025, critical-read): non-lossy dynamic update + 각 fact `valid_from`/`valid_to` 명시 — **edge-level freshness**. DMR 94.8% (vs MemGPT 93.4%).
- **A-MEM** (Xu 2025, K1-δ에서도 인용): 새 note 생성 시 기존 note attribute(timestamp/context/keywords/tags/embedding) memory evolution. graphify ingest의 "rewire" 알고리즘 모델.

### Algorithm foundation (1종)
- **Leiden** (Traag-Waltman-van Eck Sci Reports 2019): Louvain의 **disconnected community 25%** 결함 증명 + refinement step. graphify M3 FAIL이 알고리즘적으로 발생할 수 있는 이유 + resolution parameter 민감도 baseline.

### LLM-as-Judge / Evaluator separation (5종)
- **MT-Bench / Chatbot Arena** (Zheng NeurIPS 2023, foundational): GPT-4 judge가 human crowd >80% agreement. **position bias / verbosity bias / self-enhancement bias** 3 실패 모드 정식화. §5.3 H3 judge N≥5 출발점.
- **PoLL** (Verga 2024, critical-read): single judge 대신 **diverse model family 다수**. intra-model bias ↓ + 7× 저렴 + 6 dataset에서 단일 large 우수. **§5.3 H3 evaluator separation(cross-family)의 주 근거**.
- **Self-preference bias** (Panickssery 2024, critical-read): LLM judge가 자기 출력 인식 + 더 높게 평가. self-recognition ↔ self-preference linear correlation. **"H1b idea 제안 모델은 그 평가 금지" rule의 실증**.
- **LLM-as-Judge Survey** (Gu 2024-2025): inter-judge agreement 지표(Pearson/Spearman/**Cohen's κ**/Krippendorff's α) 적용 조건 정리. κ ≥ 0.6 문턱의 survey 정합 근거.
- **Judge's Verdict** (Han 2025, recent-SOTA): 54 LLM judge × Cohen's κ + z-score two-step. **"correlation은 높지만 systematic bias 있는 judge"** 문제 명시 — correlation 대신 **actual agreement(κ)**로 옮겨야 함을 주장. **§5.3 H3 falsifier에서 correlation 아닌 κ 사용의 가장 강한 근거**.
- **Empirical study** (Yamauchi 2025): BIGGENBench·EvalBiasBench. **명시적 evaluation criteria**가 신뢰도 가장 큰 결정 요인 + non-deterministic sampling이 human alignment에 유리 + CoT는 criteria 명확하면 이득 미미. FM1~FM4 rubric 설계의 실증.

### κ 해석 (2종)
- **Landis & Koch 1977** (Biometrics, foundational): κ tier 표 (slight 0-0.20 / fair 0.21-0.40 / moderate 0.41-0.60 / **substantial 0.61-0.80** / almost perfect 0.81-1.00). **§5.3 "κ ≥ 0.6" 문턱의 직접 출처**.
- **McHugh 2012** (Biochemia Medica, critical-read): Landis-Koch 한계 지적 — **prevalence·marginal bias가 κ 왜곡**. 의료는 0.80+ 요구, 그 외는 0.60 충분. **"κ ≥ 0.6 + marginal bias 체크 병행" 판단 근거**.

### Active triage / Hallucination taxonomy / HELM (3종)
- **LLMs in the Loop** (Kholodna 2024): token entropy로 uncertain 선별 → LLM annotator → 사람은 high-uncertainty만. **42× 비용 절감**. §7.3 AMBIGUOUS triage 2단계 routing 비용 근거.
- **Hallucination Survey** (Huang 2024, ACM TOIS): **factuality** vs **faithfulness**(instruction · context · logical inconsistency) 2-level taxonomy. **FM1~FM4 매핑**: FM1 factuality / FM2 context faithfulness / FM3 logical inconsistency / FM4 instruction deviation.
- **HELM** (Liang Stanford CRFM 2022, foundational): 30 model × 16 scenario × 7 metric(accuracy/calibration/robustness/fairness/bias/toxicity/efficiency). PoLL HELM식 metric plane 분리 원칙 차용.

## 본 프로젝트와의 연결 (Direction Evidence)

### L2 substrate spec deferred items 4개 직접 backing

| spec deferred item | K2-ε 채택 결정 |
|--------------------|----------------|
| D-1 per-node freshness | Zep edge-level `valid_from`/`valid_to` + LightRAG incremental update + A-MEM memory evolution. graphify에 freshness metadata layer 추가 |
| D-2 confidence_score | Ahmed 2026 GOLD/SILVER/BRONZE + 0.95/0.85/0.70 (Codex 3-round에서 alternative B 채택, K2-ε 인용 그대로) |
| D-3 ranking calibration | nano-graphrag knob 모델 + GraphRAG-Bench structural metric 정렬 + Leiden resolution parameter 명시 |
| D-4 `L2.memory.recall` semantics | Microsoft GraphRAG community-based retrieval + LightRAG dual-level (low/high) → `query_text + budget_tokens` ≤ 32000 토큰 contract |

### §5.3 H3 falsifier 강화 evidence

| H3 rule | K2-ε 근거 |
|---------|-----------|
| judge N ≥ 5 | Zheng 2023 MT-Bench (GPT-4 single judge baseline) → Verga 2024 PoLL (panel) |
| evaluator separation cross-family | Panickssery 2024 self-preference + Verga 2024 PoLL family diversity |
| Cohen's κ ≥ 0.6 | Landis-Koch 1977 substantial 문턱 + McHugh 2012 marginal bias 체크 + Han 2025 actual-agreement >> correlation |
| FM1~FM4 rubric | Huang 2024 taxonomy (factuality + faithfulness 3 sub) + Yamauchi 2025 explicit criteria |
| H1b idea 제안 모델 평가 금지 | Panickssery 2024 self-recognition ↔ self-preference linear correlation |

### graphify M3 lint 기준 외부 정렬

- **non-isolated nodes ratio**: GraphRAG-Bench structural metric으로 정식화 — 본 프로젝트 lint threshold 외부 정렬 근거
- **disconnected community**: Leiden 알고리즘 자체가 community 25% disconnected 가능성 내재 (Traag 2019) — graphify M3 FAIL은 random failure가 아닌 알고리즘적 결과
- **AMBIGUOUS triage**: safishamsi/graphify의 3-tier 모델 + Snorkel denoise + Kholodna active triage = §7.3 workflow 완성

## 미해결 / 추가 탐색

- **graphify resolution parameter 민감도**: Leiden community 결과가 resolution에 어떻게 반응하는지 본 프로젝트 그래프(현재 9 페이지) 실측 필요. 향후 100+ 페이지 시점에 재측정.
- **κ ≥ 0.6 marginal bias 보강**: McHugh 2012의 prevalence·marginal bias 체크를 H3 implementation에 어떻게 인코딩할지 — 코드 단계에서 결정.
- **PoLL 모델 family 명단**: Anthropic / OpenAI / Google / Meta / Mistral 등 어느 family가 panel 5명에 들어갈지 운영 결정. 본 프로젝트는 Codex(OpenAI) + Claude(Anthropic) 기 사용 — 추가 3 family 결정 필요.

## 교차 참조

- [[k1-delta-research-memory-evidence]] — A-MEM이 양 축에 인용. K1-δ는 패러다임, K2-ε는 confidence·freshness 산식.
- [[k1-alpha-llm-for-hdl-evidence]] — H1b novelty seam에 대한 본 페이지의 평가 인프라.
- [[k1-beta-agentic-eda-evidence]] — agent reward 신호의 evaluator 분리 정합 (cross-family).
- [[eda-flow-report-reading]] — `.rpt` 해석 능력이 confidence tier 평가의 input.
- (pending) `[[k2-zeta-l1-runtime-evidence]]` — L1 freshness가 본 페이지의 graph freshness layer와 cross-link.
- (pending) `[[k2-eta-patch-mutation-evidence]]` — reversible-patch + AMBIGUOUS triage workflow.
- (pending) `[[k2-theta-benchmark-license-evidence]]` — HELM-style metric plane이 MLPerf Tiny v1.3 평가 plane과 연결.

## Source

- 원본: `raw/papers/k2-epsilon-graph-quality-judge.md` (2026-04-22 collected, 21 sources, confidence: medium → spec 채택 시 high)
- decision_anchors: `raw/imports_manifest.yaml`
- 직접 backing: `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` (Codex 3-round review에서 본 evidence를 §3 alternative B 채택으로 인용)
