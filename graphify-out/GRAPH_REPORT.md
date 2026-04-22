# Graph Report - .  (2026-04-22)

## Corpus Check
- 93 files · ~128,040 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 327 nodes · 402 edges · 35 communities detected
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_L1 Process — Derived Spec|L1 Process — Derived Spec]]
- [[_COMMUNITY_Spec|Spec]]
- [[_COMMUNITY_lockfile.py|lockfile.py]]
- [[_COMMUNITY_main()|main()]]
- [[_COMMUNITY_StageTiming|StageTiming]]
- [[_COMMUNITY_conftest.py|conftest.py]]
- [[_COMMUNITY__base()|_base()]]
- [[_COMMUNITY_s3.py|s3.py]]
- [[_COMMUNITY_Integrated Research Program Design Spec|Integrated Research Program Design Spec]]
- [[_COMMUNITY_test_graph_integrity.py|test_graph_integrity.py]]
- [[_COMMUNITY_Issues Tracker README|Issues Tracker README]]
- [[_COMMUNITY_graphify cross-link bridge manifest|graphify cross-link bridge manifest]]
- [[_COMMUNITY_test_orfs_runner.py|test_orfs_runner.py]]
- [[_COMMUNITY_make_session()|make_session()]]
- [[_COMMUNITY_TraceLogger|TraceLogger]]
- [[_COMMUNITY_test_run_stage.py|test_run_stage.py]]
- [[_COMMUNITY_get_ddb_write_count()|get_ddb_write_count()]]
- [[_COMMUNITY_Project Context — 3-Layer +|Project Context — 3-Layer +]]
- [[_COMMUNITY_test_cli_submit_status.py|test_cli_submit_status.py]]
- [[_COMMUNITY_sfn.py|sfn.py]]
- [[_COMMUNITY_L1 Process Implementation Plan|L1 Process Implementation Plan]]
- [[_COMMUNITY_resolveContext()|resolveContext()]]
- [[_COMMUNITY_test_librelane_runner.py|test_librelane_runner.py]]
- [[_COMMUNITY_test_metric_collector.py|test_metric_collector.py]]
- [[_COMMUNITY_Phase 0 A1 — CMOS|Phase 0 A1 — CMOS]]
- [[_COMMUNITY_NetworkStack.ts|NetworkStack.ts]]
- [[_COMMUNITY_test_sanity.py|test_sanity.py]]
- [[_COMMUNITY_AGENTS.md repository guidelines|AGENTS.md repository guidelines]]
- [[_COMMUNITY_Project Glossary|Project Glossary]]
- [[_COMMUNITY_graphify Codex 3-round Review Log|graphify Codex 3-round Review Log]]
- [[_COMMUNITY_scriptsgraph_integrity_check.py|scripts/graph_integrity_check.py]]
- [[_COMMUNITY_srcsemi_design_runnercli.py|src/semi_design_runner/cli.py]]
- [[_COMMUNITY_EDA AI Research Agent Handoff|EDA AI Research Agent Handoff]]
- [[_COMMUNITY_graphify Adoption Plan|graphify Adoption Plan]]
- [[_COMMUNITY_Phase 1a Wiki Skill Engine|Phase 1a Wiki Skill Engine]]

## God Nodes (most connected - your core abstractions)
1. `L1 Process — Derived Spec (2026-04-20)` - 19 edges
2. `Spec` - 15 edges
3. `FlowParameters` - 11 edges
4. `Integrated Research Program Design Spec (2026-04-19)` - 11 edges
5. `_StrictBase` - 10 edges
6. `Metrics` - 10 edges
7. `_base()` - 8 edges
8. `StageTiming` - 8 edges
9. `graphify cross-link bridge manifest` - 8 edges
10. `_write_graph()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Unit tests for the metric-collector entrypoint.  metric_collector_main is import` --uses--> `Metrics`  [INFERRED]
  tests/runner/test_metric_collector_main.py → src/semi_design_runner/schemas.py
- `Codex #8: parser implementation must live in metrics.py only.` --uses--> `Metrics`  [INFERRED]
  tests/runner/test_metric_collector_main.py → src/semi_design_runner/schemas.py
- `test_parse_reports_clean_case()` --calls--> `parse_reports()`  [INFERRED]
  tests/runner/test_metrics.py → src/semi_design_runner/metrics.py
- `test_parse_reports_handles_missing_power()` --calls--> `parse_reports()`  [INFERRED]
  tests/runner/test_metrics.py → src/semi_design_runner/metrics.py
- `_base()` --calls--> `FlowParameters`  [INFERRED]
  tests/runner/test_validate_spec.py → src/semi_design_runner/schemas.py

## Hyperedges (group relationships)
- **L1 Kill Gates KG-A~KG-F** —  [EXTRACTED 0.95]

## Communities

### Community 0 - "L1 Process — Derived Spec"
Cohesion: 0.08
Nodes (25): G0 bootstrap → G1 transition status table, ContainerStack, L1 Architecture (Local semi-run CLI → AWS SFN/Fargate), CDK Stacks (Network/Storage/Container/Compute/Workflow/Observability), CDK Test Strategy (snapshot + cdk-nag + assertions), ContainerStack (ECR × 3 immutable tags), DynamoDB schema (Runs/Generations/Candidates/Events), Docker images (orfs-runner / librelane-runner / metric-collector) (+17 more)

### Community 1 - "Spec"
Cohesion: 0.12
Nodes (28): BaseModel, ExperimentalParameters, FlowParameters, Metrics, Pydantic v2 schemas for L1 Process layer.  All models inherit from _StrictBase w, Signoff metrics parsed from .rpt/.def. All-or-nothing: constructed only when sig, L1.run(spec_uri) output.      Invariants:       - metrics_uri is ALWAYS a valid, Internal base for L1 schemas.      Rejects unknown keys to prevent silent layer (+20 more)

### Community 2 - "lockfile.py"
Cohesion: 0.18
Nodes (14): canonical_yaml(), compute_l1_sha(), load_lockfile(), _project_l1(), Lockfile verification with L1/L3-readiness scope separation.  The L1 scope hash, Sort keys and drop null values so L3 nulls do not affect hash., Keep only L1-scope commit_shas + container_digests + pdk_digests., _strip_nulls() (+6 more)

### Community 3 - "main()"
Cohesion: 0.16
Nodes (13): main(), Container ENTRYPOINT target for the semi/metric-collector image.  Wrapped by doc, _resolve_path(), parse_reports(), Parse Yosys/OpenROAD/LibreLane report files into the Metrics schema.  This modul, Unit tests for the metric-collector entrypoint.  metric_collector_main is import, Codex #8: parser implementation must live in metrics.py only., _seed_fixtures() (+5 more)

### Community 4 - "StageTiming"
Cohesion: 0.24
Nodes (14): BudgetExceededError, check_accumulated_budget(), check_planned_budget(), Budget guard logic shared by KG-F F1 (pre-RunTask rejection) and F2 (post-stage, Raised by either F1 or F2 guard. Message names which one., Per-stage Fargate timing + cost. One entry per completed stage in RunArtifact.co, StageTiming, _make_spec() (+6 more)

### Community 5 - "conftest.py"
Cohesion: 0.15
Nodes (9): _docker_available(), initialized_wiki(), _page(), Shared fixtures for semi_design_runner tests., Empty directory intended to become a wiki root., Pre-populated wiki tree for sync/lint tests., Helper to write a page file., _require_docker() (+1 more)

### Community 6 - "_base()"
Cohesion: 0.28
Nodes (11): Exception, _base(), test_aes_rejected(), test_gcd_librelane_passes(), test_gcd_orfs_passes(), test_ibex_rejected(), test_rejection_message_lists_allowed_designs(), G1-scope validator (spec §12 + overview §8 G1).  Pure function — no AWS or IO de (+3 more)

### Community 7 - "s3.py"
Cohesion: 0.18
Nodes (10): download_final(), put_spec(), put_with_retention(), S3 operations for L1 runner.  `put_with_retention` implements the per-object ret, Write spec.yaml to staging prefix (no retention — staging is mutable)., Download the final/ prefix mirror to local dest dir., src/semi_design_runner/aws/__init__.py, test_download_final_mirrors_prefix() (+2 more)

### Community 8 - "Integrated Research Program Design Spec"
Cohesion: 0.15
Nodes (12): K1 α — LLM for HDL, K1 β — Agentic EDA, K1 δ — Research Memory, K1 direction report (52 sources), K1 γ — Open-Source EDA, K2 ε — Graph quality / LLM-as-judge, K2 η — Patch + mutation, K2 θ — Benchmark + license (+4 more)

### Community 9 - "test_graph_integrity.py"
Cohesion: 0.33
Nodes (9): graphify exports use NetworkX node_link_graph format with 'links' key., test_ambiguous_ratio_exceeded_fails(), test_ambiguous_ratio_within_threshold_passes(), test_clean_graph_passes(), test_dangling_edge_fails(), test_empty_graph_fails(), test_networkx_links_key_supported(), test_orphan_node_fails() (+1 more)

### Community 10 - "Issues Tracker README"
Cohesion: 0.2
Nodes (10): Issue 001: Planner structural mutation operator, Issue 002: Fargate Spot retry/fallback, Issue 003: Wiki ingest automation (resolved by graphify), Issue 004: Observability dashboard scope, Issues Tracker README, Document Structure Review (graphify transition cleanup), graphify S1 Evaluation Report, README/issue003/glossary still show wiki legacy paths (+2 more)

### Community 11 - "graphify cross-link bridge manifest"
Cohesion: 0.22
Nodes (9): graphify cross-link bridge manifest, §1 CDK Jest test ↔ Stack bridges, §2 Docker test ↔ Dockerfile bridges, §3 __init__.py ↔ package bridges, §4 K1 paper ↔ spec grounding bridges, §5 K2 paper ↔ spec grounding bridges, §6 Phase 0 learning session chain, §7 README ↔ spec bridges (+1 more)

### Community 12 - "test_orfs_runner.py"
Cohesion: 0.25
Nodes (4): Build test for the ORFS runner image.  This test performs an actual `docker buil, Codex review #8: Verilator must NOT be shipped in G1 orfs-runner., test_orfs_runner_has_no_verilator(), tests/docker/__init__.py

### Community 14 - "make_session()"
Cohesion: 0.36
Nodes (6): make_client(), make_session(), boto3 session + client factory with SSO profile and adaptive retries., test_make_client_applies_retry_config(), test_make_session_allows_none_profile(), test_make_session_uses_named_profile()

### Community 15 - "TraceLogger"
Cohesion: 0.36
Nodes (4): test_trace_logger_appends_jsonl(), test_trace_logger_timestamps_each_line(), JSONL trace logger for infrastructure-level events.  Kept separate from L3 reaso, TraceLogger

### Community 16 - "test_run_stage.py"
Cohesion: 0.36
Nodes (6): Contract tests for docker/entrypoints/run-stage.sh.  These tests exercise the sh, _run(), test_missing_run_id_exits_2(), test_simulate_spot_reclaim_exits_143(), test_staging_layout_created(), tests/entrypoints/__init__.py

### Community 17 - "get_ddb_write_count()"
Cohesion: 0.32
Nodes (6): get_ddb_write_count(), put_candidate_with_count(), DynamoDB wrappers. Candidates.ddb_write_count is the app-level counter used by K, test_get_counter_returns_int_value(), test_get_counter_returns_zero_when_item_missing(), test_put_candidate_uses_add_to_increment_counter()

### Community 18 - "Project Context — 3-Layer +"
Cohesion: 0.25
Nodes (8): 4-plane × 3-layer architecture summary, Project Context — 3-Layer + 4-plane AutoResearch, 2-tier search strategy (Template + Open Ideation), LLM Wiki Rule Exception (graphify 전환), semi-run Python orchestrator CLI, Query: v2 ↔ Phase 1a disjoint 입증, scripts/graph_integrity_check.py::check_graph_integrity(), src/semi_design_runner/cli.py::main (semi-run)

### Community 19 - "test_cli_submit_status.py"
Cohesion: 0.29
Nodes (1): tests/runner/__init__.py

### Community 20 - "sfn.py"
Cohesion: 0.33
Nodes (5): describe_execution(), Step Functions wrappers. Execution name = run_id for easy tracing., start_execution(), test_describe_execution_pass_through(), test_start_execution_serializes_payload_and_names_by_run_id()

### Community 21 - "L1 Process Implementation Plan"
Cohesion: 0.29
Nodes (7): L1 Process Implementation Plan, L1 Phase B CDK Draft, L1 Phase C Docker Draft, CDK TypeScript 6 stacks, Docker images (orfs-runner/librelane-runner/metric-collector), semi-run CLI (python runner), Rationale: Verilator absent (G1 no sim)

### Community 22 - "resolveContext()"
Cohesion: 0.33
Nodes (2): resolveContext(), buildApp()

### Community 23 - "test_librelane_runner.py"
Cohesion: 0.33
Nodes (3): Build and ENTRYPOINT contract tests for semi/librelane-runner.  The LibreLane pr, Same KG-D contract as orfs-runner: SIMULATE_SPOT_RECLAIM=1 → exit 143., test_librelane_runner_honors_simulate_spot_reclaim()

### Community 24 - "test_metric_collector.py"
Cohesion: 0.4
Nodes (1): End-to-end container test for semi/metric-collector.

### Community 25 - "Phase 0 A1 — CMOS"
Cohesion: 0.8
Nodes (5): Phase 0 Curriculum, Phase 0 A1 — CMOS, Phase 0 A2 — Logic gates, Phase 0 A3 — Clock & timing, Phase 0 A4 — Combinational vs sequential

### Community 26 - "NetworkStack.ts"
Cohesion: 0.5
Nodes (1): NetworkStack

### Community 27 - "test_sanity.py"
Cohesion: 0.5
Nodes (1): tests/__init__.py

### Community 28 - "AGENTS.md repository guidelines"
Cohesion: 0.5
Nodes (4): Build/test/dev make commands, Coding style (Ruff, Py3.12, 100-char), AGENTS.md repository guidelines, Testing guidelines (pytest, tmp_path)

### Community 29 - "Project Glossary"
Cohesion: 0.5
Nodes (4): Project Glossary, Operator concept, Reversible patch, Skill library

### Community 30 - "graphify Codex 3-round Review Log"
Cohesion: 0.5
Nodes (4): graphify Codex 3-round Review Log, Codex Round 1 (L2 interfaces compat), Codex Round 2 (tier semantic gap), Codex Round 3 (evidence path doesn't harm H1/H3 falsifier)

### Community 31 - "scripts/graph_integrity_check.py"
Cohesion: 0.67
Nodes (2): scripts/__init__.py, scripts/graph_integrity_check.py

### Community 32 - "src/semi_design_runner/cli.py"
Cohesion: 0.67
Nodes (2): src/semi_design_runner/__init__.py, src/semi_design_runner/cli.py

### Community 34 - "EDA AI Research Agent Handoff"
Cohesion: 1.0
Nodes (2): EDA AI Research Agent Handoff (superseded), Autotuning-first handoff (superseded)

### Community 35 - "graphify Adoption Plan"
Cohesion: 1.0
Nodes (2): graphify Adoption Plan, scripts/graph_integrity_check.py (new)

### Community 36 - "Phase 1a Wiki Skill Engine"
Cohesion: 1.0
Nodes (2): Phase 1a Wiki Skill Engine Plan, Phase 1a CLI tools (wiki-init/wiki-sync/wiki-lint)

## Knowledge Gaps
- **94 isolated node(s):** `graphify exports use NetworkX node_link_graph format with 'links' key.`, `Empty directory intended to become a wiki root.`, `Pre-populated wiki tree for sync/lint tests.`, `Helper to write a page file.`, `Build test for the ORFS runner image.  This test performs an actual `docker buil` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `test_cli_submit_status.py`** (7 nodes): `test_artifacts_downloads_final_prefix()`, `test_cost_emits_budget_guard_check()`, `test_status_joins_ddb_and_sfn()`, `test_submit_starts_execution_and_prints_arn()`, `tests/runner/__init__.py`, `__init__.py`, `test_cli_submit_status.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `resolveContext()`** (6 nodes): `resolveContext()`, `semi-design.ts`, `jest.config.ts`, `app-context.ts`, `app.test.ts`, `buildApp()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `test_metric_collector.py`** (5 nodes): `built_image()`, `End-to-end container test for semi/metric-collector.`, `test_metric_collector_produces_metrics_json()`, `test_metric_collector_simulate_spot_reclaim()`, `test_metric_collector.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `NetworkStack.ts`** (4 nodes): `NetworkStack.ts`, `NetworkStack.test.ts`, `NetworkStack`, `.constructor()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `test_sanity.py`** (4 nodes): `test_version()`, `tests/__init__.py`, `__init__.py`, `test_sanity.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `scripts/graph_integrity_check.py`** (3 nodes): `scripts/__init__.py`, `scripts/graph_integrity_check.py`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `src/semi_design_runner/cli.py`** (3 nodes): `src/semi_design_runner/__init__.py`, `src/semi_design_runner/cli.py`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `EDA AI Research Agent Handoff`** (2 nodes): `EDA AI Research Agent Handoff (superseded)`, `Autotuning-first handoff (superseded)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `graphify Adoption Plan`** (2 nodes): `graphify Adoption Plan`, `scripts/graph_integrity_check.py (new)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Phase 1a Wiki Skill Engine`** (2 nodes): `Phase 1a Wiki Skill Engine Plan`, `Phase 1a CLI tools (wiki-init/wiki-sync/wiki-lint)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Metrics` connect `Spec` to `main()`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `Spec` connect `Spec` to `StageTiming`, `_base()`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `_StrictBase` connect `Spec` to `StageTiming`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Spec` (e.g. with `RejectedNotInG1Scope` and `G1-scope validator (spec §12 + overview §8 G1).  Pure function — no AWS or IO de`) actually correct?**
  _`Spec` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `FlowParameters` (e.g. with `_base()` and `test_flow_parameters_all_optional_none()`) actually correct?**
  _`FlowParameters` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify exports use NetworkX node_link_graph format with 'links' key.`, `Empty directory intended to become a wiki root.`, `Pre-populated wiki tree for sync/lint tests.` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `L1 Process — Derived Spec` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._