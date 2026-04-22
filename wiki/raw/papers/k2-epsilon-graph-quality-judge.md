---
type: raw-import
axis: epsilon
title: "K2 축별 자료 — Graph quality · LLM-as-judge · human triage"
date: 2026-04-22
phase: K2
curator: claude-opus-4-7
source_count: 21
intent: "Codex 3-round follow-up에서 L2 파생 spec으로 deferred된 per-node freshness, confidence_score 산식, ranking calibration + H3 falsifier 강화(Cohen's κ, FM rubric, evaluator separation)를 뒷받침하는 자료."
---

# K2 Axis ε — Graph Quality · LLM-as-Judge · Human Triage

## Meta lists
- https://github.com/CSHaitao/Awesome-LLMs-as-Judges — LLM-as-judge 논문·벤치마크 큐레이션 (매주 갱신). 축 ε의 inter-judge agreement·self-preference·panel 논문 발굴 허브.
- https://github.com/DEEP-PolyU/Awesome-GraphRAG — GraphRAG 계열 surveys/benchmarks/opensource 모음. 그래프 품질 지표 follow-up 탐색용.

## Resources

### 1. From Local to Global: A Graph RAG Approach to Query-Focused Summarization (Edge et al., Microsoft, 2024)
- URL: https://arxiv.org/abs/2404.16130
- Tag: [foundational, critical-read, graph-quality]
- WHAT: Microsoft GraphRAG 원 논문. LLM으로 entity·relation 추출 → Leiden community detection → 계층적 community summary를 사전 생성하는 2-stage index 구조를 제시한다. 본 프로젝트 graphify 스킬의 상위 디자인 참조원이며, §3.2 L2.memory의 community-based retrieval 근거다. 추출 품질이 60~85% 수준이라는 후속 evidence는 confidence_score 재도입 기준 수립의 baseline으로 쓴다.

### 2. LightRAG: Simple and Fast Retrieval-Augmented Generation (Guo et al., EMNLP 2025)
- URL: https://arxiv.org/abs/2410.05779
- Tag: [open-source-impl, graph-quality, recent-SOTA]
- WHAT: Dual-level (low/high) retrieval과 incremental update algorithm을 포함한 경량 GraphRAG 변종. 특히 **incremental update**가 핵심 — 새 문서가 들어왔을 때 전체 재색인 없이 그래프를 갱신하는 메커니즘은 본 프로젝트 per-node freshness·temporal decay 설계(§3.2 L2.memory deferred spec)에 직접 참조된다.

### 3. nano-graphrag — minimal hackable GraphRAG (gusye1234, 2024-2026)
- URL: https://github.com/gusye1234/nano-graphrag
- Tag: [open-source-impl, production-pattern]
- WHAT: Microsoft GraphRAG의 ~800-line 재구현. `global_max_consider_community` 같은 커뮤니티 랭킹 파라미터를 명시적으로 노출하여 Leiden 결과 중 실제로 쿼리에 쓸 top-K 커뮤니티를 튜닝 가능한 구조. graphify M3 FAIL (고립 community) 완화책 설계 시 cross-links bridge 구현 레퍼런스로 사용.

### 4. safishamsi/graphify — knowledge graph skill (2025-2026)
- URL: https://github.com/safishamsi/graphify
- Tag: [open-source-impl, production-pattern, critical-read]
- WHAT: 본 프로젝트가 /graphify 스킬로 채택한 구현체. 모든 relation을 EXTRACTED / INFERRED(confidence score) / AMBIGUOUS(for review) 세 tier로 태깅하는 provenance 모델이 핵심. §7.3 AMBIGUOUS triage workflow 설계의 upstream이며, GOLD/SILVER/BRONZE 재도입 논의의 실체 레퍼런스.

### 5. GraphRAG-Bench: Challenging Benchmark for GraphRAG (2025)
- URL: https://arxiv.org/abs/2506.02404
- Tag: [benchmark, graph-quality, recent-SOTA]
- WHAT: GraphRAG pipeline 전 구간(graph construction → retrieval → generation) holistic 평가 프레임. Node count, non-isolated nodes ratio 같은 **structure-based metric**을 정식화하여 그래프 구조 품질을 정량화한다. 본 프로젝트 "graphify M3 (non-isolated 비율) ≥ threshold" 같은 lint 기준을 외부 벤치마크에 정렬할 근거.

### 6. The Provenance Gap in Clinical AI: Evidence-Traceable Temporal Knowledge Graphs (Ahmed et al., 2026)
- URL: https://arxiv.org/abs/2604.17114
- Tag: [critical-read, graph-quality, production-pattern]
- WHAT: 임상 도메인 TKG에서 **GOLD/SILVER/BRONZE tier + 고정 confidence value(0.95/0.85/0.70)** 를 제안한 최근 논문. 각 tier 정의(cross-tier confirmed · multi-model consensus · single-source)는 우리 `confidence_score` 재도입 및 AMBIGUOUS 재분류 기준의 직접 템플릿이다. Temporal KG로 freshness·validity period까지 함께 다루는 점이 §5.3 H3 evidence bundle과 호환.

### 7. From Louvain to Leiden: guaranteeing well-connected communities (Traag, Waltman, van Eck, Scientific Reports 2019)
- URL: https://arxiv.org/abs/1810.08473
- Tag: [foundational, graph-quality]
- WHAT: Leiden 알고리즘 seminal 논문. Louvain의 **disconnected community** 결함(최대 25% badly connected, 16% disconnected)을 증명하고, 각 community의 모든 subset이 locally optimally assigned임을 보장하는 refinement 단계를 도입. graphify M3 FAIL이 "disconnected community"를 내재적으로 낳을 수 있는 알고리즘적 근거이며, resolution parameter 민감도 분석의 baseline.

### 8. Zep: A Temporal Knowledge Graph Architecture for Agent Memory (Rasmussen et al., 2025)
- URL: https://arxiv.org/abs/2501.13956
- Tag: [recent-SOTA, critical-read, graph-quality]
- WHAT: Graphiti 엔진 기반 agent memory. **non-lossy dynamic update + 각 fact의 validity period(from/to) 명시**가 핵심 — 오래된 사실을 지우지 않고 "무효화 시각"을 기록하여 per-node freshness를 edge-level로 구현한다. DMR 벤치 94.8% vs MemGPT 93.4%. 본 프로젝트 L2.memory의 freshness·timestamp 모델링의 가장 가까운 최신 레퍼런스.

### 9. A-MEM: Agentic Memory for LLM Agents (Xu et al., arXiv 2502.12110, 2025)
- URL: https://arxiv.org/abs/2502.12110
- Tag: [recent-SOTA, production-pattern]
- WHAT: Zettelkasten 기반 agentic memory. 새 note 생성 시 기존 note의 attribute(timestamp, context, keywords, tags, embedding)를 **memory evolution**으로 갱신한다. δ축 자료(#8)에서 이미 인용됐지만, ε축에서는 per-node freshness 관점(각 note가 독립적으로 attribute 업데이트되는 구조)으로 재인용. graphify ingest 시 기존 노드를 "rewire"하는 알고리즘 설계의 직접 모델.

### 10. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., NeurIPS 2023)
- URL: https://arxiv.org/abs/2306.05685
- Tag: [foundational, critical-read, rubric]
- WHAT: LLM judge의 seminal 논문. GPT-4 judge가 human crowd와 >80% agreement(human-human agreement와 같은 수준)를 달성함을 보이면서 position bias, verbosity bias, self-enhancement bias 세 실패 모드를 정식화. 본 프로젝트 §5.3 H3 judge N≥5 설계의 출발점이며, FM rubric 3대 실패 유형 중 정량화된 baseline.

### 11. Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models (Verga et al., 2024)
- URL: https://arxiv.org/abs/2404.18796
- Tag: [evaluator-separation, critical-read]
- WHAT: 단일 GPT-4 judge 대신 **서로 다른 모델 패밀리의 작은 LLM 다수(PoLL)** 로 평가. intra-model bias 감소 + 7× 저렴 + 6개 데이터셋에서 단일 대형 judge 대비 우수. 본 프로젝트 §5.3 H3 "evaluator separation(cross-family)" 조건의 주 근거 — Anthropic/OpenAI/Google/Meta 패밀리 혼합 패널을 정당화한다.

### 12. LLM Evaluators Recognize and Favor Their Own Generations (Panickssery et al., 2024)
- URL: https://arxiv.org/abs/2404.13076
- Tag: [evaluator-separation, critical-read]
- WHAT: LLM judge가 **자신이 생성한 출력**을 인식하고 더 높게 평가하는 self-preference bias를 측정 가능한 현상으로 증명. self-recognition 능력과 self-preference 강도 사이에 linear correlation. 본 프로젝트에서 "H1b novelty idea를 제안한 모델이 그 평가에 참여 금지" 룰의 실증적 근거.

### 13. A Survey on LLM-as-a-Judge (Gu et al., arXiv 2411.15594, 2024-2025)
- URL: https://arxiv.org/abs/2411.15594
- Tag: [survey, evaluator-separation, rubric]
- WHAT: "How can reliable LLM-as-a-Judge systems be built?"을 축으로 한 최신 survey. inter-judge agreement 지표로 Pearson/Spearman/**Cohen's κ/Krippendorff's α** 각각의 적용 조건을 정리. §5.3 H3 "Cohen's κ ≥ 0.6" 문턱을 survey 관행과 정렬할 근거.

### 14. Judge's Verdict: A Comprehensive Analysis of LLM Judge Capability Through Human Agreement (Han et al., arXiv 2510.09738, 2025)
- URL: https://arxiv.org/abs/2510.09738
- Tag: [recent-SOTA, rubric, evaluator-separation]
- WHAT: 54개 LLM judge를 Cohen's κ + z-score two-step으로 평가. "correlation만 높고 systematic bias가 있는 judge" 문제를 명시적으로 다뤄, correlation에서 **actual agreement**로 지표를 옮겨야 함을 주장. Tier 1(human-like pattern) 23 모델 / super-consistent 4 모델. 본 프로젝트 H3 falsifier에서 correlation 대신 κ를 쓰는 이유의 가장 강한 레퍼런스.

### 15. An Empirical Study of LLM-as-a-Judge: How Design Choices Impact Evaluation Reliability (Yamauchi et al., arXiv 2506.13639, 2025)
- URL: https://arxiv.org/abs/2506.13639
- Tag: [recent-SOTA, rubric]
- WHAT: BIGGENBench·EvalBiasBench로 evaluation design·decoding·CoT 효과를 측정. 주요 발견 — **명시적 evaluation criteria**가 신뢰도의 가장 큰 결정 요인, non-deterministic sampling이 human alignment에 유리, CoT는 criteria가 분명하면 이득 미미. 본 프로젝트 FM1~FM4 rubric 작성 시 criteria 명시 방식 결정의 실증 근거.

### 16. The Measurement of Observer Agreement for Categorical Data (Landis & Koch, Biometrics 1977)
- URL: https://pubmed.ncbi.nlm.nih.gov/843571/
- Tag: [foundational, rubric]
- WHAT: Cohen's κ 해석 랜드마크. 0.00–0.20 slight / 0.21–0.40 fair / 0.41–0.60 moderate / **0.61–0.80 substantial** / 0.81–1.00 almost perfect. 본 프로젝트 §5.3 H3 "κ ≥ 0.6" 문턱의 출처이자, "substantial 이상" 이라는 서술의 authoritative reference.

### 17. Interrater reliability: the kappa statistic (McHugh, Biochemia Medica 2012)
- URL: https://www.biochemia-medica.com/en/journal/22/3/10.11613/BM.2012.031
- Tag: [foundational, rubric, critical-read]
- WHAT: Landis-Koch 해석 테이블의 **한계를 지적**하고 실무적 해석(prevalence·marginal bias가 κ를 왜곡)을 정리. κ ≥ 0.80 이상을 요구해야 하는 도메인(의료)과 0.60로 충분한 도메인을 구분. 본 프로젝트에서 "κ ≥ 0.6을 넘더라도 marginal bias 체크가 병행되어야 한다"는 판단 근거.

### 18. Snorkel: Rapid Training Data Creation with Weak Supervision (Ratner et al., VLDB 2017)
- URL: https://arxiv.org/abs/1711.10160
- Tag: [foundational, production-pattern]
- WHAT: labeling function들이 노이지·상관된 라벨을 내놓을 때 **ground truth 없이 denoise**하는 data programming 패러다임. 본 프로젝트에서 LLM extractor 여러 개가 서로 다른 결과를 낼 때 AMBIGUOUS 판정 후 human triage로 넘기기 전, 먼저 label model로 denoise하는 단계의 근거.

### 19. LLMs in the Loop: Leveraging LLM Annotations for Active Learning in Low-Resource Languages (Kholodna et al., arXiv 2404.02261, 2024)
- URL: https://arxiv.org/abs/2404.02261
- Tag: [production-pattern, recent-SOTA]
- WHAT: token-level entropy로 uncertain sample을 고른 뒤 LLM annotator에 위임, 사람은 high-uncertainty 영역만 확인. 순수 human annotation 대비 **42× 비용 절감**. 본 프로젝트 §7.3 AMBIGUOUS triage에서 "LLM-retry → 여전히 uncertain이면 human"의 2단계 routing 비용 근거.

### 20. A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges (Huang et al., ACM TOIS 2024, arXiv 2311.05232)
- URL: https://arxiv.org/abs/2311.05232
- Tag: [survey, rubric, critical-read]
- WHAT: LLM 실패를 **factuality hallucination** (vs real-world fact) vs **faithfulness hallucination** (vs user input / self-consistency; 하위로 instruction · context · logical inconsistency)으로 2-level taxonomize. 본 프로젝트 FM1~FM4 rubric 설계의 상위 taxonomy 근거 — FM1(factuality) / FM2(context faithfulness) / FM3(logical inconsistency) / FM4(instruction deviation)로 매핑 가능.

### 21. Holistic Evaluation of Language Models — HELM (Liang et al., Stanford CRFM, arXiv 2211.09110, 2022)
- URL: https://arxiv.org/abs/2211.09110
- Tag: [foundational, evaluator-separation, benchmark]
- WHAT: 30개 모델을 16개 core scenario × 7 metric(accuracy · calibration · robustness · fairness · bias · toxicity · efficiency)로 평가하는 전면 프레임. "같은 프롬프트·같은 채점 기준으로 여러 모델 패밀리를 병렬 평가"하는 운영 패턴의 표준. 본 프로젝트 PoLL 구성 시 HELM식 metric plane 분리 원칙(한 지표 ≠ 한 모델 가족으로 결정)을 차용.
