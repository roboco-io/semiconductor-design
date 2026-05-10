---
title: "K1-δ: Research Memory Systems + LLM Wikis + AutoResearch — Direction Evidence"
type: synthesis
tags: [k1, research-memory, llm-wiki, autoresearch, voyager, ades, hybrid-search]
status: active
confidence: medium
created: 2026-05-09
updated: 2026-05-09
sources:
  - raw/papers/k1-delta-research-memory.md
  - raw/imports_manifest.yaml
related_specs:
  - docs/superpowers/specs/2026-04-19-integrated-research-program-design.md  # §3 L2 substrate
  - docs/superpowers/specs/2026-04-23-L2-substrate-design.md  # L2 파생
  - docs/superpowers/specs/2026-04-22-graphify-adoption-design.md  # superseded by 2026-05-09 wiki-first 결정
related_decisions:
  - "2026-05-09 wiki-first 전환 (CLAUDE.md 컨텍스트 관리 정책)"
---

# K1-δ: Research Memory + LLM Wikis — Direction Evidence

본 프로젝트의 **L2 Substrate layer**(typed-frontmatter memory + reversible-patch skill library + wiki-first 컨텍스트 라우팅)의 13개 source 근거. **2026-05-09 wiki-first 전환 결정 자체의 1차 학술적 근거**가 본 페이지에 집중됨 (self-referential).

## Meta-Framing — 본 페이지의 위치

| 항목 | 내용 |
|------|------|
| 본 페이지의 source #1 | Karpathy LLM Wiki gist — 본 위키가 따르는 패턴의 origin |
| 본 페이지가 적용된 위키 | 본 페이지 자신을 포함한 `wiki/*.md` 컴파일 레이어 |
| 결정 근거 | [Karpathy 72-run 벤치마크](https://roboco.io/posts/karpathy-llm-wiki-72-run-benchmark/) — 토큰 −53.6%, 시간 −39.3%, 품질 +6% (p<0.01) |
| 이전 결정 | 2026-04-22 graphify-only 전환 (현재 hybrid 보조로 격하) |

## Converged Patterns (commodity)

| Pattern | 대표 source | 본 프로젝트 채택 |
|---------|-------------|------------------|
| 3-tier memory (working/episodic/archival) | Letta(MemGPT), Mem0, A-MEM | L2 typed-frontmatter memory에 매핑 |
| Hybrid BM25 + vector + LLM rerank | qmd, LanceDB | wiki-first 라우팅 + qmd 보조 (skill graceful degrade) |
| LLM-maintained markdown corpus | Karpathy Wiki, A-MEM | **본 위키 자체** |
| Reflection-style failure log | Reflexion, Voyager skill lib | L2 reversible-patch skill_library |

## Still Open Problems (novelty seam)

| # | 문제 | 본 프로젝트 매핑 |
|---|------|------------------|
| 1 | **위키 규모 모순 해소·provenance** — "두 source가 어긋날 때 lint 단계에서 깔끔히 merge"는 미해결 | L2.lint.check 확장 영역 (orphan/dangling 외 contradiction lint) |
| 2 | **Long-running 실험 프로그램 메모리** — chat turn이 아닌 hours-to-days 멀티모달 artifact (LOCOMO 미커버) | 본 프로젝트 L2 + L1 artifact lake (S3) |
| 3 | **Negative-result recall** — 실패가 first-class 메모리로 인덱스되지 않아 agent가 같은 실패 재제안 | L2 memory schema의 failure object (typed) |

## Source 카테고리

### Wiki / 컨텍스트 관리 (5종 — 본 페이지의 직접 모태)
- **Karpathy LLM Wiki** (#1, foundational): 3-layer (raw → wiki → CLAUDE.md schema) + 3-op (ingest/query/lint). 본 위키 기본 구조의 origin.
- **LLM Wiki v2 / Ghumare** (#2): Karpathy 패턴의 production-grade 확장 — contradiction resolution, ingest fan-out 과부하 해결.
- **tobi/qmd** (#3): local BM25+vector+LLM rerank, "remember later" loop 패턴. **llm-wiki skill의 hybrid search 백엔드.**
- **LanceDB hybrid search** (#4): file-native vector DB + Tantivy FTS. wiki가 plain file 한도를 넘으면 substrate.
- **apple/embedding-atlas** (#5, 2025): browser-local 인터랙티브 임베딩 탐색. wiki 감사용.

### Memory 아키텍처 (3종)
- **Letta** (#6): DB-persisted core/archival/recall, OS-paging.
- **Mem0** (#7, 2025): extract-consolidate-retrieve, p95 latency·token-cost 우세 (LOCOMO).
- **A-MEM** (#8, 2025, critical-read): Zettelkasten 동적 링크 + memory evolution. **Karpathy lint-and-rewire wiki의 가장 가까운 학술 analog.**

### Self-improving agent (3종)
- **Voyager** (#9, foundational, critical-read): ever-growing executable skill library + automatic curriculum + self-verification. **본 프로젝트 L2 reversible-patch skill_library의 직접 모델.**
- **Reflexion** (#10): episodic verbal-reflection, weight update 없는 실패 누적.
- **Generative Agents** (#11, UIST'23): memory stream + reflection + recency·importance·relevance scoring.

### Meta-search / Agent system (2종)
- **ADAS** (#12, ICLR 2025, critical-read): Meta Agent Search — meta-agent가 새 agent를 ever-growing archive에 program. **본 프로젝트 AutoResearch 루프의 직접 모델.**
- **Anthropic Multi-agent Research System** (#13, 2025-06): lead-researcher + parallel subagent + prompt-self-repair, tool description rewriting (−40% task time). **이 K1 run 자체가 이미 4-parallel subagent 패턴 사용.**

### 제외 (1종)
- "Memory for Autonomous LLM Agents survey (arXiv 2603.07670)" — URL 형식 의심, 검증 실패.

## 본 프로젝트와의 연결 (Direction Evidence)

### Underserved Niche — "Karpathy + Voyager × EDA artifacts"

13개 source가 합쳐 가리키는 publishable seam:

> Karpathy-wiki **durability** + Voyager-style **executable memory**를 **EDA report artifacts**(`*.rpt`, `.def`, STA slack)에 specialize. 상용 PPA를 이기지 않고도 academic/process novelty 가능 영역.

3개 직접 매핑:

1. **`*.rpt`/`.def`/STA-slack을 typed-frontmatter structured memory 객체로** — `lint`가 "이 PnR 실패는 2주 전과 동일"을 감지.
2. **RTL+constraints 위 reversible-patch skill library** — 각 skill = 검증된 Yosys/OpenROAD transform + signed-off report. Voyager 정신.
3. **AutoResearch loop의 archive = wiki 자체** — ADAS-style meta-search에서 discovered agent design AND discovered microarchitecture가 모두 first-class wiki page.

### Spec / DSE 영향

| 결정 | K1-δ 근거 | 어디 |
|------|-----------|------|
| L2 substrate에 typed-frontmatter memory + skill_library + lint.check 3-API | source #1, #8, #9 | spec §3.2 contract table |
| **wiki-first 컨텍스트 라우팅 (2026-05-09)** | source #1 + Karpathy 72-run 벤치마크 | CLAUDE.md L13 정책 갱신 |
| graphify를 cross-component path 보조로 격하 | source #4 + 벤치마크 (graphify가 종합 task에서 wiki 미달) | CLAUDE.md L96 |
| llm-wiki skill의 qmd hybrid search 백엔드 | source #3 + #4 | wiki/index.md 라우팅 규칙 4 |
| `lint.check` orphan/dangling/AMBIGUOUS≤0.3 외 contradiction lint 추가 검토 | source #2, #8 (open problem #1) | spec L2 §lint extension |
| L1 artifact lake가 hours-to-days artifact 메모리 | source open problem #2 | spec §3 L1.run + S3 |
| failure를 typed memory로 (Iter N+1이 N의 실패를 회수) | source #9, #10 + open problem #3 | L2 memory schema |
| AutoResearch reasoning trace를 1차 deliverable로 | source #12, #13 + α/β/γ landscape 결론 | spec §1 intent |

## 미해결 / 추가 탐색

- **Contradiction lint** 알고리즘 선택 — A-MEM의 동적 링크 evolution을 어떻게 단순화해 본 위키에 적용할지 (G2 직전 결정).
- **qmd vs LanceDB 도입 시점** — 위키 페이지 수 임계점(~500) 도달 시점 (현재 ~10페이지, far below). [llm-wiki skill](../../../.claude/skills/documentation/llm-wiki/SKILL.md) 의 graceful degrade 정책 그대로.
- **AutoResearch reasoning trace의 publishable 형식** — single PPA number 대신 무엇을 논문 figure/table로 만들지는 G3 직전 결정.

## 교차 참조

- [[k1-alpha-llm-for-hdl-evidence]] — RTL agent SOTA가 본 페이지의 memory 패턴을 채택하지 않아 H1b의 차별화 axis가 됨
- [[k1-beta-agentic-eda-evidence]] — ORFS-agent가 memoryless라는 open problem이 L2 substrate 차별화 근거
- [[k1-gamma-opensource-eda-evidence]] — `.rpt`/`.def` artifact의 출처 (sky130A + LibreLane stack)
- [[phase-0-eda-operator-lens]] — `.rpt` 해석 능력이 본 페이지 typed-memory의 전제
- [[clock-and-timing]] — STA slack object의 의미
- [[fsm-and-pipeline]] — reversible-patch가 적용될 RTL 단위
- [[k2-epsilon-graph-quality-judge-evidence]] — typed-memory 패턴이 4 deferred items (per-node freshness, confidence_score 산식, ranking calibration, recall semantics) + LLM-as-judge κ ≥ 0.6 falsifier로 spec-binding

## Source

- 원본: `raw/papers/k1-delta-research-memory.md` (2026-04-19 collected, confidence: low → medium)
- 13개 외부 source의 decision_anchors는 `raw/imports_manifest.yaml`
- **본 페이지의 self-referential 결정**: `wiki/log.md` 2026-05-09 항목 + CLAUDE.md L13 정책 갱신 (둘 다 Karpathy 72-run 벤치마크 근거)
