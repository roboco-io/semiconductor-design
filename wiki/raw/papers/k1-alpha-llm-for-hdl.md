---
type: raw-axis-summary
axis: alpha
title: "α. LLM for HDL — K1 Resource Survey"
date: 2026-04-19
status: collected
confidence: low
last_verified: 2026-04-19
curator: claude-opus-4-7
tags: [k1, llm-for-hdl, rtl-generation, testbench, hdl-benchmark, multi-agent]
source_count: 12
---

# α. LLM for HDL — K1 Resource Survey

## Resources

### 1. VerilogEval — Evaluating Large Language Models for Verilog Code Generation (2023, V2 2025)
- URL: https://arxiv.org/abs/2309.07544
- Tag: [benchmark, foundational]
- WHAT: De-facto pass@k benchmark, 156 problems from HDLBits. V2 (Pinckney et al., 2025) adds robust spec-to-RTL infra. Cited by nearly every paper below.

### 2. RTLLM — Open-Source Benchmark for Design RTL Generation (ASP-DAC 2024; 2.0 update)
- URL: https://github.com/hkust-zhiyao/RTLLM · paper https://arxiv.org/pdf/2308.05345
- Tag: [benchmark, open-source-impl]
- WHAT: 29+ designs with NL spec, reference RTL, testbenches; scores syntax / function / PPA. Paired with VerilogEval in virtually all SOTA evaluations.

### 3. CVDP — Comprehensive Verilog Design Problems (NVIDIA, 2025)
- URL: https://arxiv.org/abs/2506.14074 · repo https://github.com/NVlabs/cvdp_benchmark
- Tag: [benchmark, critical-read]
- WHAT: 783 human-authored problems across 13 categories (RTL, verif, debug, assertions, comprehension) in non-agentic and agentic formats. SOTA tops out at 34% pass@1 (Claude 3.7). Adopted by Si2's LLM Benchmarking Coalition — **this is the hard benchmark where novelty is still possible.**

### 4. ChipNeMo — Domain-Adapted LLMs for Chip Design (NVIDIA, 2023)
- URL: https://arxiv.org/abs/2311.00176
- Tag: [foundational]
- WHAT: Domain-adaptive tokenization + continued pretraining + RAG on LLaMA2. Established the "domain-adapt > generic LLM" pattern.

### 5. RTLCoder — Fully Open-Source LLM-Assisted RTL Generation (TCAD 2024/2025)
- URL: https://arxiv.org/abs/2312.08617 · repo https://github.com/hkust-zhiyao/RTL-Coder
- Tag: [open-source-impl]
- WHAT: 7B model + 27k-sample dataset + full training pipeline, beats GPT-3.5 and GPT-4 (VerilogEval-Machine). One of few fully-open stacks.

### 6. VeriGen — Large Language Model for Verilog Code Generation (TODAES 2024)
- URL: https://arxiv.org/abs/2308.00708 · code https://github.com/shailja-thakur/VGen
- Tag: [foundational, open-source-impl]
- WHAT: First widely-used open Verilog corpus + fine-tuned CodeGen variants (345M–16B). Common starting point for fine-tuning baselines.

### 7. MAGE — Multi-Agent Engine for Automated RTL Code Generation (2024)
- URL: https://arxiv.org/abs/2412.07822 · project https://stable-lab.github.io/MAGE/
- Tag: [multi-agent, recent-SOTA]
- WHAT: First open multi-agent RTL system; high-temperature candidate sampling + Verilog-state checkpointing; 95.7% on VerilogEval-Human V2.

### 8. VerilogCoder — Autonomous Verilog Coding Agents with Graph-based Planning (AAAI 2025)
- URL: https://d1qx31qr3h6wln.cloudfront.net/publications/2408.08927v1_arXiv.pdf
- Tag: [multi-agent]
- WHAT: Task-and-Circuit Relation Graph planner + AST-based waveform tracing agent for targeted debug. Representative of "agent + simulator-in-the-loop" wave.

### 9. AssertLLM — Hardware Verification Assertions from Design Specs via Multi-LLMs (ASP-DAC 2025)
- URL: https://arxiv.org/abs/2402.00386 · repo https://github.com/hkust-zhiyao/AssertLLM
- Tag: [multi-agent, open-source-impl]
- WHAT: Three-stage LLM pipeline turning full spec documents (incl. waveform diagrams) into SVAs; 89% syntactic+functional correctness. Key *verification* reference.

### 10. EvolVE — Evolutionary Search for LLM-based Verilog Generation and Optimization (2026)
- URL: https://arxiv.org/abs/2601.18067
- Tag: [recent-SOTA, critical-read]
- WHAT: MCTS vs Idea-Guided Refinement analysis on chip tasks + Structured Testbench Generation. 98.1% VerilogEval v2, 92% RTLLM v2; up to 66% PPA reduction on industry-scale suite. Direct conceptual neighbor of our "Open Ideation" track.

### 11. RL with Testbench Feedback for Verilog LLMs (2025) + CorrectBench (2024)
- URL: https://arxiv.org/abs/2504.15804 · https://arxiv.org/html/2411.08510v1
- Tag: [recent-SOTA]
- WHAT: First trains a Verilog LLM with VCS-based RL reward; second raises testbench-gen pass from 52%→70% via self-correction. Cover testbench + self-repair axis.

### 12. Surveys — LLM for Verilog Literature Review (2025) + LLMs for EDA (2025)
- URL: https://arxiv.org/abs/2512.00020 · https://arxiv.org/abs/2508.20030
- Tag: [survey]
- WHAT: Systematic review of 102 papers, 27 benchmarks, 34 datasets; documents 2023→2025 explosion (6→29→64 papers/yr) and taxonomizes agentic paradigms. Best single "get-oriented-fast" read.

### Meta resource lists
- https://github.com/CatIIIIIIII/RTL-LLM-Paper-List — continuously curated
- https://github.com/Thinklab-SJTU/Awesome-LLM4EDA — broader EDA+LLM

## Landscape Snapshot

- **Saturated**: Module-level combinational/simple-FSM RTL generation on VerilogEval-Human and RTLLM v2 (multiple 2025–2026 agents report 90%+ pass@1). Incremental gains no longer publishable on their own. Same for "just fine-tune another Verilog LLM" without a new training signal.

- **Open problems**:
  1. CVDP-hard / agentic tasks still cap at ~34% pass@1, especially *RTL reuse* and *verification*.
  2. Closing the loop from spec → RTL → testbench → sign-off as one PPA-aware artifact (not just functional) is unsolved — EvolVE is an early shot.
  3. Non-Verilog HDLs (Chisel, PyRTL, SpinalHDL, MLIR-CIRCT) have almost no benchmarks and weak model support.
  4. Trustworthy self-repair with formal guarantees (Proof2Silicon direction) is nascent.

- **Small-team novelty window**:
  A project that couples **open EDA sign-off feedback (Yosys/OpenROAD `.rpt` + STA slack + DRC) as the reward/critique signal** for an agentic loop — rather than only simulator pass/fail — hits an underexplored seam. Combined with Karpathy-style "Open Ideation" over Gemmini-like accelerator templates on CVDP-agentic tasks, framed as an AutoResearch process study, this directly aligns with what the surveys flag as missing: *PPA-aware, sign-off-grounded, multi-agent HDL synthesis with a publishable operator/process story.*
