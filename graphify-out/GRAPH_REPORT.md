# Graph Report - .  (2026-04-22)

## Corpus Check
- 93 files · ~80,599 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 547 nodes · 757 edges · 40 communities detected
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Spec|Spec]]
- [[_COMMUNITY_sync_index()|sync_index()]]
- [[_COMMUNITY_Project glossary|Project glossary]]
- [[_COMMUNITY_K1 Core Concepts 20 (frozen pre-scan)|K1 Core Concepts 20 (frozen pre-scan)]]
- [[_COMMUNITY__base()|_base()]]
- [[_COMMUNITY_parse_file()|parse_file()]]
- [[_COMMUNITY_K1 β. Agentic EDA + Autotuning survey|K1 β. Agentic EDA + Autotuning survey]]
- [[_COMMUNITY_A4 — Combinational vs Sequential + FSM + Pipeline|A4 — Combinational vs Sequential + FSM + Pipeline]]
- [[_COMMUNITY_program.md operating constitution|program.md operating constitution]]
- [[_COMMUNITY_graphify S1 Evaluation Report|graphify S1 Evaluation Report]]
- [[_COMMUNITY_lockfile.py|lockfile.py]]
- [[_COMMUNITY_init_wiki()|init_wiki()]]
- [[_COMMUNITY_K1 γ. Open-Source EDA Stack + Accelerator Templates survey|K1 γ. Open-Source EDA Stack + Accelerator Templates survey]]
- [[_COMMUNITY_make_client()|make_client()]]
- [[_COMMUNITY_G1 L1 Process Gate (KG-A~KG-E)|G1 L1 Process Gate (KG-A~KG-E)]]
- [[_COMMUNITY_conftest.py|conftest.py]]
- [[_COMMUNITY_H1 Primary Hypothesis|H1 Primary Hypothesis]]
- [[_COMMUNITY_TraceLogger|TraceLogger]]
- [[_COMMUNITY_test_orfs_runner.py|test_orfs_runner.py]]
- [[_COMMUNITY_test_librelane_runner.py|test_librelane_runner.py]]
- [[_COMMUNITY_test_run_stage.py|test_run_stage.py]]
- [[_COMMUNITY_test_metric_collector.py|test_metric_collector.py]]
- [[_COMMUNITY_resolveContext()|resolveContext()]]
- [[_COMMUNITY_Repository guidelines for Python wiki engine|Repository guidelines for Python wiki engine]]
- [[_COMMUNITY_StorageStack|StorageStack]]
- [[_COMMUNITY_NetworkStack|NetworkStack]]
- [[_COMMUNITY_ContainerStack|ContainerStack]]
- [[_COMMUNITY_Semiconductor design domain wiki engine.|Semiconductor design domain wiki engine.]]
- [[_COMMUNITY_Rationale — Semantic Gap Between Tier and Claim Validity|Rationale — Semantic Gap Between Tier and Claim Validity]]
- [[_COMMUNITY_MLPerf Tiny v1.3|MLPerf Tiny v1.3]]
- [[_COMMUNITY_CVDP-hard Agentic Tasks (34% pass@1)|CVDP-hard Agentic Tasks (34% pass@1)]]
- [[_COMMUNITY_K1 Core Concepts 20 (M2 Coverage Target)|K1 Core Concepts 20 (M2 Coverage Target)]]
- [[_COMMUNITY_Rollback Matrix (per-stage revert)|Rollback Matrix (per-stage revert)]]
- [[_COMMUNITY_HUGI for Silicon (Hurry Up and Get Idle)|HUGI for Silicon (Hurry Up and Get Idle)]]
- [[_COMMUNITY_Cross-LLM Consensus (Claude vs Codex)|Cross-LLM Consensus (Claude vs Codex)]]
- [[_COMMUNITY_graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)|graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)]]
- [[_COMMUNITY_graphify MCP Server (L2.memory.recall backend)|graphify MCP Server (L2.memory.recall backend)]]
- [[_COMMUNITY_G0 Program Bootstrap Gate|G0 Program Bootstrap Gate]]
- [[_COMMUNITY_l1_lockfile_sha separation from full_lockfile_sha|l1_lockfile_sha separation from full_lockfile_sha]]
- [[_COMMUNITY__StrictBase with extra=forbid (Pydantic schema)|_StrictBase with extra=forbid (Pydantic schema)]]

## God Nodes (most connected - your core abstractions)
1. `Spec` - 18 edges
2. `sync_index()` - 18 edges
3. `lint_wiki()` - 17 edges
4. `K1 γ. Open-Source EDA Stack + Accelerator Templates survey` - 16 edges
5. `Project glossary` - 16 edges
6. `K1 δ. Research Memory + LLM Wiki + AutoResearch survey` - 14 edges
7. `K1 β. Agentic EDA + Autotuning survey` - 12 edges
8. `make_page()` - 11 edges
9. `FlowParameters` - 11 edges
10. `K1 α. LLM for HDL survey` - 11 edges

## Surprising Connections (you probably didn't know these)
- `AutoResearch loop pattern` --semantically_similar_to--> `program.md operating constitution`  [INFERRED] [semantically similar]
  docs/eda_agent_handoff.md → wiki/program/program.md
- `Unit tests for the metric-collector entrypoint.  metric_collector_main is import` --uses--> `Metrics`  [INFERRED]
  tests/runner/test_metric_collector_main.py → src/semi_design_runner/schemas.py
- `Codex #8: parser implementation must live in metrics.py only.` --uses--> `Metrics`  [INFERRED]
  tests/runner/test_metric_collector_main.py → src/semi_design_runner/schemas.py
- `AWS 3-plane architecture (Control/Execution/Knowledge)` --semantically_similar_to--> `4-plane architecture (Local/AWS/Tool/Knowledge)`  [INFERRED] [semantically similar]
  docs/eda_agent_handoff.md → CLAUDE.md
- `Rationale: sign-off-grounded agentic HDL synthesis is an underexplored seam` --rationale_for--> `2-tier search strategy (Template DSE + Open Ideation)`  [INFERRED]
  wiki/raw/papers/k1-alpha-llm-for-hdl.md → CLAUDE.md

## Hyperedges (group relationships)
- **3-layer program decomposition (L1/L2/L3)** — claudemd_3_layer_architecture, glossary_l1_process, glossary_l2_substrate, glossary_l3_content [EXTRACTED 0.95]
- **K1 four-axis knowledge survey (α/β/γ/δ)** — k1_alpha_llm_for_hdl, k1_beta_agentic_eda, k1_gamma_opensource_eda, k1_delta_research_memory [EXTRACTED 0.95]
- **Phase 0 Branch A learning pipeline A1→A2→A3→A4** — phase0_a1_cmos, phase0_a2_logic_gates, phase0_a3_clock_timing, phase0_a4_combinational_sequential [EXTRACTED 0.90]
- **Three K1 Seams Converge into Integrated Program** — k1_direction_report_seam_a, k1_direction_report_seam_b, k1_direction_report_seam_c, k1_direction_report_integrated_program, integrated_research_program_design_3_layer [EXTRACTED 1.00]
- **H1a/H1b/H1c Triple Hypothesis Ensemble** — integrated_research_program_design_h1a_finding_reuse, integrated_research_program_design_h1b_non_knob_patch, integrated_research_program_design_h1c_cold_start, integrated_research_program_design_h1_primary, integrated_research_program_design_canonical_decision_table [EXTRACTED 1.00]
- **Three L1 Images Share run-stage.sh ENTRYPOINT** — l1_phasec_docker_draft_orfs_runner_image, l1_phasec_docker_draft_librelane_runner_image, l1_phasec_docker_draft_metric_collector_image, l1_phasec_docker_draft_run_stage_sh [EXTRACTED 1.00]

## Communities

### Community 0 - "Spec"
Cohesion: 0.07
Nodes (51): BaseModel, auth_group(), main(), semi-run CLI entry point. Subcommands operate on Spec/RunArtifact lifecycle.  `i, L1 Process runner CLI., AWS authentication helpers., BudgetExceededError, check_accumulated_budget() (+43 more)

### Community 1 - "sync_index()"
Cohesion: 0.09
Nodes (39): make_page(), BrokenLink, _check_broken_links(), _check_low_confidence(), _check_missing_fields(), _check_orphans(), lint_wiki(), LintReport (+31 more)

### Community 2 - "Project glossary"
Cohesion: 0.06
Nodes (45): 2-tier search strategy (Template DSE + Open Ideation), 3-layer architecture (L1/L2/L3), 4-plane architecture (Local/AWS/Tool/Knowledge), Archived 2026-04-17 single-loop spec, H1b non-knob structural patch (novelty metric), 2026-04-19 overview spec reference, Project Context — Report-Grounded Vibe-Coded AutoResearch, EDA AI Research Agent 핸드오프 (superseded) (+37 more)

### Community 3 - "K1 Core Concepts 20 (frozen pre-scan)"
Cohesion: 0.07
Nodes (41): L2 Interface v2 (graphify-backed), graphify Adoption Design Spec, K1 Core Concepts 20 (frozen pre-scan), 3-Layer Structure (L1 Process / L2 Substrate / L3 Content), Appendix C — Gemmini Knob Exclusion List, Rationale — Autotuning-only MVP Dropped (ORFS-agent exists), H1b Non-knob Structural Patch, L1 Process Layer (+33 more)

### Community 4 - "_base()"
Cohesion: 0.1
Nodes (24): artifacts_cmd(), init_cmd(), get_ddb_write_count(), put_candidate_with_count(), DynamoDB wrappers. Candidates.ddb_write_count is the app-level counter used by K, download_final(), put_spec(), put_with_retention() (+16 more)

### Community 5 - "parse_file()"
Cohesion: 0.1
Nodes (22): MissingFieldsError, parse_file(), YAML frontmatter parsing for wiki pages., Raised when required frontmatter fields are missing., Return (frontmatter_dict, body_text). Empty dict if no frontmatter., Raise MissingFieldsError if any required field is missing., validate_required(), main() (+14 more)

### Community 6 - "K1 β. Agentic EDA + Autotuning survey"
Cohesion: 0.1
Nodes (25): Initial MVP — ORFS autotuning focus (superseded), AssertLLM — verification assertions from spec, ChipNeMo — Domain-Adapted LLMs for Chip Design, CVDP — Comprehensive Verilog Design Problems (NVIDIA), EvolVE — evolutionary search for Verilog (2026), K1 α. LLM for HDL survey, MAGE — Multi-Agent Engine for RTL, Rationale: sign-off-grounded agentic HDL synthesis is an underexplored seam (+17 more)

### Community 7 - "A4 — Combinational vs Sequential + FSM + Pipeline"
Cohesion: 0.1
Nodes (24): Learning lens — EDA operator, not chip designer, open_pdks (sky130A/sky130B/gf180mcuD), A1 — Transistors / CMOS, CMOS complementary pair — low static current, Leakage / power wall — why INT8 & DVFS, MOSFET as voltage-controlled switch, sky130 130nm open PDK rationale, Combinational vs Sequential logic (+16 more)

### Community 8 - "program.md operating constitution"
Cohesion: 0.1
Nodes (22): Canonical Decision Table (§5.3) publish/reframed/kill, H3 reasoning-trace recovery hypothesis, Reversible patch (glossary), semi-run CLI, program.md operating constitution, R1. reversible-patch-only rule, R2. every claim backed by evidence, R3. negative result as first-class asset (+14 more)

### Community 9 - "graphify S1 Evaluation Report"
Cohesion: 0.11
Nodes (22): Rationale — Strangler Swap over Big-Bang Rewrite, Codex 3-Round Review for v2 Spec, graph_integrity_check.py, Phase S1 — graphify Evaluate, Phase S2 — Spec Revise, Phase S3 — Code Swap, Phase S4 — Doc & Skill Cleanup, Strangler Swap 4-Stage Strategy (+14 more)

### Community 10 - "lockfile.py"
Cohesion: 0.17
Nodes (15): lockfile_verify_cmd(), canonical_yaml(), compute_l1_sha(), load_lockfile(), _project_l1(), Lockfile verification with L1/L3-readiness scope separation.  The L1 scope hash, Sort keys and drop null values so L3 nulls do not affect hash., Keep only L1-scope commit_shas + container_digests + pdk_digests. (+7 more)

### Community 11 - "init_wiki()"
Cohesion: 0.16
Nodes (16): _ensure_file(), init_wiki(), main(), Initialize wiki directory structure (idempotent)., Create wiki directory structure if missing. Idempotent., CLI: initialize a wiki directory., test_init_creates_claude_md_with_schema(), test_init_creates_subdirs() (+8 more)

### Community 12 - "K1 γ. Open-Source EDA Stack + Accelerator Templates survey"
Cohesion: 0.15
Nodes (19): Anti-reinvention principle (wrap open-source EDA), Efabless 2025-02 shutdown invalidates chipIgnite path, CFU Playground, Chipyard 1.13.0, cocotb 2.0.1, Efabless Shutdown (Feb 2025), Gemmini v0.7.1 (main only), KLayout (+11 more)

### Community 13 - "make_client()"
Cohesion: 0.14
Nodes (14): cost_cmd(), status_cmd(), submit_cmd(), make_client(), make_session(), boto3 session + client factory with SSO profile and adaptive retries., describe_execution(), Step Functions wrappers. Execution name = run_id for easy tracing. (+6 more)

### Community 14 - "G1 L1 Process Gate (KG-A~KG-E)"
Cohesion: 0.12
Nodes (17): G1 L1 Process Gate (KG-A~KG-E), KG-A LibreLane on Fargate Kill Gate, KG-B Chipyard+Gemmini Build Kill Gate, KG-C LLM SDK Quota Kill Gate, KG-D Spot Reclaim Tolerance Kill Gate, KG-E DDB Write Amplification Kill Gate, lockfile.yaml (reproducibility lockfile), Issue 002 — Fargate Spot Retry/Fallback Policy (+9 more)

### Community 15 - "conftest.py"
Cohesion: 0.17
Nodes (9): _docker_available(), initialized_wiki(), _page(), Shared fixtures for semi_design_runner tests., Empty directory intended to become a wiki root., Pre-populated wiki tree for sync/lint tests., Helper to write a page file., _require_docker() (+1 more)

### Community 16 - "H1 Primary Hypothesis"
Cohesion: 0.18
Nodes (11): §5.4 Acceptance Thresholds Summary, §5.3 Canonical Decision Table, Evaluator Separation Rule (different LLM family), H1 Primary Hypothesis, H1a Finding Reuse Rate, H1c Cold-start Failure Rate, H2 Secondary — Compounding Effect, H3 Tertiary — Reasoning Trace κ ≥ 0.6 (+3 more)

### Community 18 - "TraceLogger"
Cohesion: 0.36
Nodes (4): test_trace_logger_appends_jsonl(), test_trace_logger_timestamps_each_line(), JSONL trace logger for infrastructure-level events.  Kept separate from L3 reaso, TraceLogger

### Community 19 - "test_orfs_runner.py"
Cohesion: 0.33
Nodes (3): Build test for the ORFS runner image.  This test performs an actual `docker buil, Codex review #8: Verilator must NOT be shipped in G1 orfs-runner., test_orfs_runner_has_no_verilator()

### Community 20 - "test_librelane_runner.py"
Cohesion: 0.33
Nodes (3): Build and ENTRYPOINT contract tests for semi/librelane-runner.  The LibreLane pr, Same KG-D contract as orfs-runner: SIMULATE_SPOT_RECLAIM=1 → exit 143., test_librelane_runner_honors_simulate_spot_reclaim()

### Community 21 - "test_run_stage.py"
Cohesion: 0.53
Nodes (5): Contract tests for docker/entrypoints/run-stage.sh.  These tests exercise the sh, _run(), test_missing_run_id_exits_2(), test_simulate_spot_reclaim_exits_143(), test_staging_layout_created()

### Community 22 - "test_metric_collector.py"
Cohesion: 0.4
Nodes (1): End-to-end container test for semi/metric-collector.

### Community 24 - "resolveContext()"
Cohesion: 0.5
Nodes (2): resolveContext(), buildApp()

### Community 25 - "Repository guidelines for Python wiki engine"
Cohesion: 0.5
Nodes (4): Build/test/dev make commands, Coding style: Ruff, Python 3.12, 100-char lines, Repository guidelines for Python wiki engine, Testing guidelines (pytest, tmp_path, no touching wiki/)

### Community 26 - "StorageStack"
Cohesion: 0.67
Nodes (1): StorageStack

### Community 27 - "NetworkStack"
Cohesion: 0.67
Nodes (1): NetworkStack

### Community 28 - "ContainerStack"
Cohesion: 0.67
Nodes (1): ContainerStack

### Community 31 - "Semiconductor design domain wiki engine."
Cohesion: 1.0
Nodes (1): Semiconductor design domain wiki engine.

### Community 32 - "Rationale — Semantic Gap Between Tier and Claim Validity"
Cohesion: 1.0
Nodes (2): Rationale — Semantic Gap Between Tier and Claim Validity, graphify 3-Tier (EXTRACTED/INFERRED/AMBIGUOUS)

### Community 44 - "MLPerf Tiny v1.3"
Cohesion: 1.0
Nodes (1): MLPerf Tiny v1.3

### Community 45 - "CVDP-hard Agentic Tasks (34% pass@1)"
Cohesion: 1.0
Nodes (1): CVDP-hard Agentic Tasks (34% pass@1)

### Community 46 - "K1 Core Concepts 20 (M2 Coverage Target)"
Cohesion: 1.0
Nodes (1): K1 Core Concepts 20 (M2 Coverage Target)

### Community 47 - "Rollback Matrix (per-stage revert)"
Cohesion: 1.0
Nodes (1): Rollback Matrix (per-stage revert)

### Community 48 - "HUGI for Silicon (Hurry Up and Get Idle)"
Cohesion: 1.0
Nodes (1): HUGI for Silicon (Hurry Up and Get Idle)

### Community 49 - "Cross-LLM Consensus (Claude vs Codex)"
Cohesion: 1.0
Nodes (1): Cross-LLM Consensus (Claude vs Codex)

### Community 50 - "graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)"
Cohesion: 1.0
Nodes (1): graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)

### Community 51 - "graphify MCP Server (L2.memory.recall backend)"
Cohesion: 1.0
Nodes (1): graphify MCP Server (L2.memory.recall backend)

### Community 52 - "G0 Program Bootstrap Gate"
Cohesion: 1.0
Nodes (1): G0 Program Bootstrap Gate

### Community 53 - "l1_lockfile_sha separation from full_lockfile_sha"
Cohesion: 1.0
Nodes (1): l1_lockfile_sha separation from full_lockfile_sha

### Community 54 - "_StrictBase with extra=forbid (Pydantic schema)"
Cohesion: 1.0
Nodes (1): _StrictBase with extra=forbid (Pydantic schema)

## Knowledge Gaps
- **137 isolated node(s):** `Empty directory intended to become a wiki root.`, `Pre-populated wiki tree for sync/lint tests.`, `Helper to write a page file.`, `Build test for the ORFS runner image.  This test performs an actual `docker buil`, `Codex review #8: Verilator must NOT be shipped in G1 orfs-runner.` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `test_metric_collector.py`** (5 nodes): `built_image()`, `End-to-end container test for semi/metric-collector.`, `test_metric_collector_produces_metrics_json()`, `test_metric_collector_simulate_spot_reclaim()`, `test_metric_collector.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `resolveContext()`** (4 nodes): `resolveContext()`, `semi-design.ts`, `app-context.ts`, `buildApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `StorageStack`** (3 nodes): `StorageStack.ts`, `StorageStack`, `.constructor()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `NetworkStack`** (3 nodes): `NetworkStack.ts`, `NetworkStack`, `.constructor()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `ContainerStack`** (3 nodes): `ContainerStack.ts`, `ContainerStack`, `.constructor()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Semiconductor design domain wiki engine.`** (2 nodes): `Semiconductor design domain wiki engine.`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Rationale — Semantic Gap Between Tier and Claim Validity`** (2 nodes): `Rationale — Semantic Gap Between Tier and Claim Validity`, `graphify 3-Tier (EXTRACTED/INFERRED/AMBIGUOUS)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MLPerf Tiny v1.3`** (1 nodes): `MLPerf Tiny v1.3`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `CVDP-hard Agentic Tasks (34% pass@1)`** (1 nodes): `CVDP-hard Agentic Tasks (34% pass@1)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `K1 Core Concepts 20 (M2 Coverage Target)`** (1 nodes): `K1 Core Concepts 20 (M2 Coverage Target)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Rollback Matrix (per-stage revert)`** (1 nodes): `Rollback Matrix (per-stage revert)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HUGI for Silicon (Hurry Up and Get Idle)`** (1 nodes): `HUGI for Silicon (Hurry Up and Get Idle)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Cross-LLM Consensus (Claude vs Codex)`** (1 nodes): `Cross-LLM Consensus (Claude vs Codex)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)`** (1 nodes): `graphify v0.4.25 (tree-sitter + Leiden + Claude subagents)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `graphify MCP Server (L2.memory.recall backend)`** (1 nodes): `graphify MCP Server (L2.memory.recall backend)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `G0 Program Bootstrap Gate`** (1 nodes): `G0 Program Bootstrap Gate`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `l1_lockfile_sha separation from full_lockfile_sha`** (1 nodes): `l1_lockfile_sha separation from full_lockfile_sha`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `_StrictBase with extra=forbid (Pydantic schema)`** (1 nodes): `_StrictBase with extra=forbid (Pydantic schema)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.