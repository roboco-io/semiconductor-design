---
type: raw-axis-summary
axis: delta
title: "δ. Research Memory Systems + LLM Wikis + AutoResearch Patterns — K1 Resource Survey"
date: 2026-04-19
status: collected
confidence: low
last_verified: 2026-04-19
curator: claude-opus-4-7
tags: [k1, research-memory, llm-wiki, autoresearch, self-improving-agent, hybrid-search]
source_count: 13
exclusions:
  - id: memory-autonomous-llm-agents-survey
    reason: "URL 2603.07670 verification failed — arXiv ID format suspicious"
---

# δ. Research Memory Systems + LLM Wikis + AutoResearch Patterns — K1 Resource Survey

## Resources

### 1. Karpathy LLM Wiki (gist, 2026-04)
- URL: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Author: Andrej Karpathy
- Tag: [foundational, critical-read]
- WHAT: Three-layer pattern (raw sources → LLM-maintained wiki → `CLAUDE.md` schema) with three ops (ingest / query / lint) replacing retrieve-at-query-time RAG with a compounding knowledge base. **This project already embraces this pattern — Phase 1a wiki engine is its implementation.**

### 2. LLM Wiki v2 — extending Karpathy with agent-memory lessons (Ghumare)
- URL: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
- Tag: [production-pattern]
- WHAT: Practitioner extension addressing contradiction resolution and ingest-fan-out overload observed in real use.

### 3. tobi/qmd — local hybrid search CLI
- URL: https://github.com/tobi/qmd
- Author: Tobi Lütke
- Tag: [hybrid-search, production-pattern]
- WHAT: Local-first BM25 + vector + LLM rerank over markdown; explicit pattern for feeding hybrid retrieval into an agent's "remember later" loop.

### 4. LanceDB hybrid search
- URL: https://www.lancedb.com/blog/hybrid-search-combining-bm25-and-semantic-search-for-better-results-with-lan-1358038fe7e6
- Tag: [hybrid-search]
- WHAT: Embedded, file-native vector DB with FTS (Tantivy) + vector + RRF / ColBERT rerank. Canonical substrate when a wiki outgrows plain files.

### 5. apple/embedding-atlas (2025)
- URLs: https://github.com/apple/embedding-atlas · https://machinelearning.apple.com/research/embedding-atlas
- Authors: Ren, Hohman, Lin, Moritz (Apple)
- Tag: [hybrid-search, production-pattern]
- WHAT: Browser-local interactive exploration of million-scale embeddings with auto-clustering — useful for auditing wiki / memory corpora.

### 6. Letta (formerly MemGPT)
- URLs: https://github.com/letta-ai/letta · https://www.letta.com/blog/agent-memory
- Tag: [memory-arch, production-pattern]
- WHAT: Stateful agents with DB-persisted core / archival / recall memory; OS-paging metaphor for unlimited effective context.

### 7. Mem0 (arXiv 2504.19413, 2025)
- URL: https://arxiv.org/abs/2504.19413
- Authors: Chhikara et al.
- Tag: [memory-arch]
- WHAT: Extract-consolidate-retrieve loop with optional graph variant; p95 latency / token-cost wins on LOCOMO.

### 8. A-MEM — Agentic Memory for LLM Agents (arXiv 2502.12110, 2025)
- URL: https://arxiv.org/abs/2502.12110
- Authors: Xu et al.
- Tag: [memory-arch, critical-read]
- WHAT: Zettelkasten-inspired dynamic linking + memory evolution — **closest academic analog to Karpathy's lint-and-rewire wiki.**

### 9. Voyager (arXiv 2305.16291)
- URL: https://arxiv.org/abs/2305.16291
- Authors: Wang et al.
- Tag: [self-improving-agent, foundational]
- WHAT: Ever-growing executable skill library + automatic curriculum + self-verification. **Canonical reversible-patch-program-as-memory paper.**

### 10. Reflexion (NeurIPS 2023, arXiv 2303.11366)
- URL: https://arxiv.org/abs/2303.11366
- Authors: Shinn et al.
- Tag: [self-improving-agent, foundational]
- WHAT: Episodic verbal-reflection buffer; failure accumulation without weight updates.

### 11. Generative Agents (UIST '23, arXiv 2304.03442)
- URL: https://arxiv.org/abs/2304.03442
- Authors: Park et al.
- Tag: [foundational, memory-arch]
- WHAT: Memory stream + reflection + retrieval scoring (recency·importance·relevance) — template for long-horizon agent recall.

### 12. ADAS — Automated Design of Agentic Systems (ICLR 2025, arXiv 2408.08435)
- URL: https://arxiv.org/abs/2408.08435
- Authors: Hu, Lu, Clune
- Tag: [self-improving-agent, critical-read]
- WHAT: Meta Agent Search — a meta-agent programs new agents into an ever-growing archive. **Directly relevant to AutoResearch over chip-design flows.**

### 13. Anthropic — How we built our multi-agent research system (2025-06)
- URL: https://www.anthropic.com/engineering/multi-agent-research-system
- Tag: [production-pattern, critical-read]
- WHAT: Lead-researcher orchestrator + parallel subagents, with prompt-self-repair and tool-description rewriting (−40% task time). **Already the pattern this K1 run used (4 parallel subagents).**

### (excluded)
- "Memory for Autonomous LLM Agents survey (arXiv 2603.07670)" — URL format suspicious; verification failed. Re-check if needed via different citation.

## Landscape Snapshot

- **Converged**:
  Three-tier memory (working / episodic / archival), hybrid BM25+vector+rerank retrieval, and LLM-maintained markdown corpora are now commodity patterns — Letta, Mem0, A-MEM, qmd all assume them. Reflection-style failure logging (Reflexion, Voyager skill library) is the default self-improvement primitive.

- **Still open**:
  1. **Contradiction resolution and provenance** at wiki scale — nobody has solved the "two sources disagree, merge them" lint step cleanly.
  2. **Memory for long-running experiment programs** (hours-to-days, multimodal artifacts, not chat turns) — LOCOMO-style benchmarks don't cover it.
  3. **Negative-result recall** — agents re-propose failed designs because failures aren't indexed as first-class memories.

- **Novelty surface for a small team at the EDA/chip-design intersection**:
  1. Treat `*.rpt` / `.def` / STA-slack artifacts as **structured memory objects** (not blobs) with typed frontmatter so lint can detect "this PnR failure is the same as 2 weeks ago."
  2. A **reversible-patch skill library over RTL+constraints** in the Voyager spirit — each skill is a verified Yosys/OpenROAD transform with its signed-off report attached.
  3. An **AutoResearch loop whose archive is the wiki itself** — ADAS-style meta-search where discovered agent designs AND discovered *microarchitectures* are both first-class wiki pages.

  **Combining Karpathy-wiki durability with Voyager-style executable memory, specialized to EDA report artifacts, is an underserved niche where academic/process novelty is achievable without beating commercial PPA.**
