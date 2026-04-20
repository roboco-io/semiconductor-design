---
type: raw-axis-summary
axis: beta
title: "β. Agentic EDA + Autotuning + ML for Chip Flows — K1 Resource Survey"
date: 2026-04-19
status: collected
confidence: low
last_verified: 2026-04-19
curator: claude-opus-4-7
tags: [k1, agentic-eda, autotuning, rl-for-chip, macro-placement, commercial-copilot]
source_count: 12
---

# β. Agentic EDA + Autotuning + ML for Chip Flows — K1 Resource Survey

## Resources

### 1. ORFS-agent — Tool-Using Agents for Chip Design Optimization (2025)
- URL: https://arxiv.org/abs/2506.08332 · code https://github.com/ABKGroup/ORFS-Agent
- Tag: [recent-SOTA, open-source-impl, critical-read]
- WHAT: Model-agnostic LLM agent drives ORFS parameter tuning via function calling, reads METRICS2.1 to skip bad configs. **~13% wirelength / effective-clock-period gain vs ORFS AutoTuner BO baseline with ~40% fewer runs** on ASAP7/SKY130HD. **This directly overlaps our previously-proposed MVP — reframing required.**

### 2. AutoEDA — EDA Flow Automation via Microservice-Based LLM Agents (2025/2026)
- URL: https://arxiv.org/abs/2508.01012
- Tag: [recent-SOTA]
- WHAT: MCP-based servers wrap EDA tools; locally fine-tuned agents handle task decomposition, tool selection, Tcl error handling for RTL-to-GDSII natural-language control. ~9.9× accuracy vs naive LLM, ~97% token reduction.

### 3. The Dawn of Agentic EDA — A Survey of Autonomous Digital Chip Design (2026)
- URL: https://arxiv.org/abs/2512.23189
- Tag: [survey]
- WHAT: Taxonomy split into Neural-Augmented Solvers vs Agentic Orchestrators; frames the problem as "constrained neuro-symbolic optimization" (Perception/Cognition/Action stack).

### 4. ORFS AutoTuner (Ray Tune-based) + METRICS2.1
- URL: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts · backing paper https://vlsicad.ucsd.edu/Publications/Conferences/388/c388.pdf · reference fork https://github.com/ieee-ceda-datc/datc-rdf-flow-tuner
- Tag: [open-source-impl, foundational]
- WHAT: The canonical open-source harness. Ray Tune backend, multiple search algorithms (random, PBT, HyperOpt), JSON-declared tunable parameters. **This is the baseline ORFS-agent beat — our comparison reference.**

### 5. AutoDMP — Automated DREAMPlace-based Macro Placement (NVIDIA, ISPD 2023)
- URL: https://research.nvidia.com/publication/2023-03_autodmp-automated-dreamplace-based-macro-placement · PDF https://d1qx31qr3h6wln.cloudfront.net/publications/AutoDMP.pdf
- Tag: [autotuner-impl, foundational]
- WHAT: GPU-accelerated concurrent macro+cell placer with MOTPE multi-objective HPO. 2.7M cells / 320 macros in 3h on DGX A100.

### 6. AlphaChip — Graph placement methodology for fast chip design (Nature 2021 + 2024 Addendum)
- URL: https://www.nature.com/articles/s41586-021-03544-w · https://www.nature.com/articles/s41586-024-08032-5
- Tag: [foundational, RL-for-chip]
- WHAT: Original RL floorplanner; 2024 Addendum formalizes "AlphaChip" label and Nature's post-publication endorsement.

### 7. The False Dawn — Reevaluating Google's RL for IC Macro Placement (arXiv 2306.09633 / CACM 2024)
- URL: https://arxiv.org/abs/2306.09633 · https://cacm.acm.org/research/reevaluating-googles-reinforcement-learning-for-ic-macro-placement/ · repo https://github.com/TILOS-AI-Institute/MacroPlacement
- Tag: [critical-read, RL-for-chip]
- WHAT: Independent reimplementation + full routing; argues AlphaChip does not beat modern SOTA placers when correctly benchmarked.

### 8. That Chip Has Sailed — Critique of Unfounded Skepticism (arXiv 2411.10053)
- URL: https://arxiv.org/abs/2411.10053
- Tag: [critical-read, RL-for-chip]
- WHAT: Google's point-by-point defense against Cheng/Kahng and Markov's meta-analysis (compute, pre-training, benchmark representativeness).

### 9. CircuitNet 2.0 (ICLR 2024)
- URL: https://openreview.net/forum?id=nMFSUjxMIl · data+code https://github.com/circuitnet/CircuitNet
- Tag: [foundational, open-source-impl]
- WHAT: 10k+ designs at 14nm with routability/IR-drop/timing labels. De-facto ML-for-EDA dataset autotuner/placement papers now benchmark against.

### 10. BO-autotuner Literature Bundle — PTPT + RankTuner + MO-TuRBO
- URL: PTPT https://ieeexplore.ieee.org/document/9758073 · RankTuner (ICCAD 2024) https://dl.acm.org/doi/10.1145/3676536.3676782 · MO-TuRBO (TODAES 2023) https://dl.acm.org/doi/10.1145/3597931
- Tag: [autotuner-impl]
- WHAT: Multi-objective BO, trust-region, preference/ranking-based tuners for commercial flow parameters. Baseline class ORFS-agent and future LLM tuners must beat.

### 11. ChipNeMo (NVIDIA, ICCAD 2023)
- URL: https://arxiv.org/abs/2311.00176
- Tag: [foundational]
- WHAT: Prototype for domain-adapted chip LLMs that later agent work (AutoEDA, ORFS-agent) assumes — EDA script generation, assistant, bug triage. (Also listed in α.)

### 12. Commercial AI Copilots (public info only)
- URLs:
  - Cadence Cerebrus AI Studio + JedAI https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/soc-implementation-and-floorplanning/cadence-cerebrus-ai-studio.html · https://www.cadence.com/en_US/home/solutions/cadence-jedai-solution.html
  - Synopsys DSO.ai + Copilot / AgentEngineer https://www.synopsys.com/ai/ai-powered-eda/dso-ai.html · https://news.synopsys.com/2025-09-03-Synopsys-Announces-Expanding-AI-Capabilities-for-its-Leading-EDA-Solutions
  - Siemens EDA AI + Solido Generative/Agentic https://www.siemens.com/en-us/products/ic/solido/solido-generative-agentic-ai/ · https://news.siemens.com/en-us/siemens-eda-ai-dac-2025/
- Tag: [commercial-copilot]
- WHAT: All three vendors positioned "agentic" by DAC 2025. Cadence reports 1000+ tapeouts with Cerebrus. **Open-source differentiation urgency rising.**

## Landscape Snapshot

- **Saturated**: Pure parameter-sweep autotuners over OpenROAD/commercial flows (yet another BO variant, yet another TuRBO flavor, yet another RL wrapper around DREAMPlace). The ~13% headroom ORFS-agent reports over BO is roughly the ceiling across PTPT/RankTuner/MO-TuRBO/AutoDMP. Adding a 14th tuner without a **new axis** is incremental.

- **Open problems**:
  1. Read DRC/STA/LEC violation reports and plan *targeted* RTL or constraint patches (not re-tune hyperparameters).
  2. Maintain memory/transfer across designs so candidate N benefits from candidate N−1 (most systems memoryless).
  3. Debate/critique generated RTL against datasheet-level spec *before* synthesis.
  4. Break out of template DSE into template-breaking microarchitecture proposals while staying physically realizable.
  5. AlphaChip dispute shows even narrow RL-for-placement isn't reliably reproducible outside Google-scale compute.

- **Novelty window for a small-team + open-source-EDA + vibe-coding + AutoResearch project**:
  1. **Karpathy-style open-ideation loop on top of ORFS-agent** — agents propose structural accelerator variants, not parameter vectors; eval harness rejects with report-level feedback.
  2. **Report-grounded agent debugging** — first-class dataset + eval of "given this `.rpt`, what's the next action?"
  3. **Multi-candidate evolutionary DSE as AutoResearch artifact** — scientific contribution = agent's *reasoning trace*, not a single PPA number. Directly aligns with "academic/process novelty" per project intent.
