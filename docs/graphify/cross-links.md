---
type: bridge-manifest
title: "graphify cross-link bridge manifest (Path B M3 완화)"
date: 2026-04-22
phase: P2
curator: claude-opus-4-7
intent: >
  graphify full rebuild 이후에도 76 orphan 노드가 남는 구조적 문제 —
  (1) CDK test 파일은 code-only라 Part B 범위 밖, (2) K1/K2 paper 노드는
  Part B가 추출하되 연결 안 함, (3) __init__.py 같은 empty symbol 파일 —
  이 문서가 해소. graphify Part B 재실행 시 본 문서의 explicit 문장을
  EXTRACTED edges로 추출해 orphan을 감소시킨다.
relation_types:
  - tests: "A 파일이 B 파일의 동작을 검증한다 (CDK Jest test ↔ stack)"
  - implements: "A 문서 섹션이 B 코드에서 구현된다"
  - grounds: "A 이론/논문 자료가 B spec 주장의 근거가 된다"
  - extends: "A 세션/개념이 B를 확장·심화한다"
  - packages: "A __init__.py가 B 패키지의 진입점"
---

# graphify cross-link bridge manifest

본 문서는 graphify AST+Part B pipeline이 놓친 cross-trench edges를 **명시적 자연어 문장**으로 기술한다. Part B subagent가 이 문서를 처리하면 각 문장을 EXTRACTED edge로 graph에 주입한다.

Node ID 규약: `{stem}_{entity}` — 소문자, non-alphanumeric은 `_`. 예: `cdk/test/ContainerStack.test.ts` → `cdk_test_containerstack_test_ts`.

## 1. CDK Jest test ↔ Stack bridges

CDK TypeScript 테스트 파일들은 상대경로 import(`import { ContainerStack } from '../lib/stacks/ContainerStack'`)가 tree-sitter-typescript AST에서 edge로 투영되지 않아 orphan 처리됐다. 각 테스트는 해당 stack을 **tests**.

- `cdk/test/ContainerStack.test.ts` **tests** `cdk/lib/stacks/ContainerStack.ts`.
- `cdk/test/NetworkStack.test.ts` **tests** `cdk/lib/stacks/NetworkStack.ts`.
- `cdk/test/StorageStack.test.ts` **tests** `cdk/lib/stacks/StorageStack.ts`.
- `cdk/test/ComputeStack.test.ts` **tests** `cdk/lib/stacks/ComputeStack.ts`.
- `cdk/test/WorkflowStack.test.ts` **tests** `cdk/lib/stacks/WorkflowStack.ts`.
- `cdk/test/app.test.ts` **tests** `cdk/bin/semi-design.ts` (CDK app entry).
- `cdk/jest.config.ts` **configures** `cdk/test/app.test.ts` (Jest test runner config).

## 2. Docker test ↔ Dockerfile bridges

- `tests/docker/test_orfs_runner.py` **tests** `docker/orfs-runner.Dockerfile`.
- `tests/docker/test_librelane_runner.py` **tests** `docker/librelane-runner.Dockerfile`.
- `tests/docker/test_metric_collector.py` **tests** `docker/metric-collector.Dockerfile`.

## 3. `__init__.py` ↔ package bridges

Empty init files have no symbols but structurally mark package boundaries.

- `src/semi_design_runner/__init__.py` **packages** `src/semi_design_runner/cli.py`.
- `src/semi_design_runner/aws/__init__.py` **packages** `src/semi_design_runner/aws/s3.py`.
- `tests/__init__.py` **packages** `tests/test_sanity.py`.
- `tests/runner/__init__.py` **packages** `tests/runner/test_cli_submit_status.py`.
- `tests/docker/__init__.py` **packages** `tests/docker/test_orfs_runner.py`.
- `tests/entrypoints/__init__.py` **packages** `tests/entrypoints/test_run_stage.py`.
- `scripts/__init__.py` **packages** `scripts/graph_integrity_check.py`.

## 4. K1 paper ↔ spec grounding bridges

K1 52 sources (4축)에서 추출된 각 paper 노드가 overview spec의 어느 주장을 뒷받침하는지 명시.

### K1 α (LLM for HDL)
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §10 `EvolVE (2026)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.1 H1b (non-knob structural patch).
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §7 `MAGE (2024)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2 (multi-agent RTL).
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §8 `VerilogCoder (AAAI 2025)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2.
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §9 `AssertLLM (ASP-DAC 2025)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.3 H3 (reasoning trace).
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §11 `RL Testbench Feedback + CorrectBench (2024/2025)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2.
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §6 `VeriGen (TODAES 2024)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2.
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` §12 `LLM for Verilog + LLMs for EDA surveys (2025)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1.
- `wiki/raw/papers/k1-alpha-llm-for-hdl.md` `Rationale — sign-off-grounded agentic HDL synthesis seam` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 1 (report-grounded).

### K1 β (Agentic EDA)
- `wiki/raw/papers/k1-beta-agentic-eda.md` §3 `Dawn of Agentic EDA survey (2026)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1.
- `wiki/raw/papers/k1-beta-agentic-eda.md` §5 `AutoDMP (NVIDIA ISPD 2023)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.1 H1 (template baseline).
- `wiki/raw/papers/k1-beta-agentic-eda.md` §10 `PTPT + RankTuner + MO-TuRBO (BO autotuner bundle)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.1 H1 (template baseline).
- `wiki/raw/papers/k1-beta-agentic-eda.md` §9 `CircuitNet 2.0 (ICLR 2024)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.1 dataset.
- `wiki/raw/papers/k1-beta-agentic-eda.md` §12 `Commercial copilots (Cadence/Synopsys/Siemens)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 "academic/process novelty vs commercial" 주장.
- `wiki/raw/papers/k1-beta-agentic-eda.md` `Rationale — novelty trace` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.3 H3.

### K1 γ (Open-Source EDA)
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §3 `Yosys 0.5x` **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Tool plane (Yosys).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §4 `Verilator 5.038/5.042` **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Tool plane (Verilator).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §5 `cocotb 2.0.1` **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Tool plane (cocotb).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §6 `KLayout` **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Tool plane (KLayout).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §13 `Apache TVM-VTA` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Layer 3 (alt accelerator template).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` §14 `CFU Playground` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Layer 3 (alt accelerator template).
- `wiki/raw/papers/k1-gamma-opensource-eda.md` `No 7nm parity note` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §2 Not "7nm 이하 공정 비교 원천 불가".

### K1 δ (Research Memory)
- `wiki/raw/papers/k1-delta-research-memory.md` §2 `LLM Wiki v2 (Ghumare)` **grounds** `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md` §1 (graphify adoption 동기).
- `wiki/raw/papers/k1-delta-research-memory.md` §3 `tobi/qmd (hybrid search)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Knowledge plane 초기안.
- `wiki/raw/papers/k1-delta-research-memory.md` §4 `LanceDB hybrid search` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Knowledge plane 초기안.
- `wiki/raw/papers/k1-delta-research-memory.md` §5 `apple/embedding-atlas` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3 Knowledge plane 초기안.
- `wiki/raw/papers/k1-delta-research-memory.md` §6 `Letta (MemGPT)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2 L2.memory.recall design.
- `wiki/raw/papers/k1-delta-research-memory.md` §7 `Mem0` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2 L2.memory.recall design.
- `wiki/raw/papers/k1-delta-research-memory.md` §10 `Reflexion (NeurIPS 2023)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2 (executable memory).
- `wiki/raw/papers/k1-delta-research-memory.md` §11 `Generative Agents (UIST 2023)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2 L2.memory.recall.
- `wiki/raw/papers/k1-delta-research-memory.md` §13 `Anthropic multi-agent research system (2025-06)` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 L3 Open-Ideation.
- `wiki/raw/papers/k1-delta-research-memory.md` `Rationale — .rpt memory novelty` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 1 (report-grounded agent operation).

## 5. K2 paper ↔ spec grounding bridges

### K2 ε (Graph quality / LLM-as-judge)
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` GraphRAG benchmark papers **ground** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §3.2 L2.memory.recall quality metrics.
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` hallucination survey **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §7.3 AMBIGUOUS triage.
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` Judge survey **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.3 R0 (evaluator separation + FM judgment).
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` Stanford HELM **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.3 H3 evaluator separation.
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` Snorkel weak supervision **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §7.3 AMBIGUOUS triage (human-in-loop).
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` LLM-loop empirical **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.3 tier admissibility vs claim validity.
- `wiki/raw/papers/k2-epsilon-graph-quality-judge.md` empirical Judge (Han et al. 2025) **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.4 Cohen's κ ≥ 0.6 threshold.

### K2 ζ (L1 runtime)
- `wiki/raw/papers/k2-zeta-l1-runtime.md` AWS Fargate Spot reliability docs **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §8 G1 KG-D (Spot reclaim).
- `wiki/raw/papers/k2-zeta-l1-runtime.md` LibreLane install guide **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §8 G1 KG-A (LibreLane 3.0.2 Fargate).
- `wiki/raw/papers/k2-zeta-l1-runtime.md` re:Invent 2025 Fargate talks **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §6.2 Fargate 200 GiB.
- `wiki/raw/papers/k2-zeta-l1-runtime.md` `Rationale — stale version drift` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §6.2 Reproducibility Lockfile (K2 ζ note).

### K2 η (Patch + mutation)
- `wiki/raw/papers/k2-eta-patch-mutation.md` AgentSkills survey **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §7.2 skill registration.
- `wiki/raw/papers/k2-eta-patch-mutation.md` AlphaChip 2024 addendum **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.1 H1 baseline comparator.
- `wiki/raw/papers/k2-eta-patch-mutation.md` EXIF lifecycle **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §13 provenance.
- `wiki/raw/papers/k2-eta-patch-mutation.md` MACO / MARCO mutation operators **ground** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.1 H1b (structural mutation).
- `wiki/raw/papers/k2-eta-patch-mutation.md` SEVerA (2026) formally guarded generative agents **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §7.2 skill signing + audit.
- `wiki/raw/papers/k2-eta-patch-mutation.md` `Rationale — triad of Voyager + EvolVE + SEVerA` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2.

### K2 θ (Benchmark + license)
- `wiki/raw/papers/k2-theta-benchmark-license.md` MLPerf Tiny v1.3 submission results **ground** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §5.3 H1c alt-benchmark.
- `wiki/raw/papers/k2-theta-benchmark-license.md` NVDLA activity status 2025-2026 **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §13 License & Provenance Gate (NVDLA exclusion).
- `wiki/raw/papers/k2-theta-benchmark-license.md` IHP SG13G2 open PDK **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §11 Efabless 대체 경로.
- `wiki/raw/papers/k2-theta-benchmark-license.md` wafer.space shuttle **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §11 Efabless 대체 경로.
- `wiki/raw/papers/k2-theta-benchmark-license.md` SLSA / SPDX provenance frameworks **ground** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §13 provenance.yaml.
- `wiki/raw/papers/k2-theta-benchmark-license.md` `Rationale — provenance gap` **grounds** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §13.

## 6. Phase 0 learning session chain

- `wiki/raw/sessions/phase-0-a1-cmos.md` **extends** `docs/learning/phase-0-curriculum.md` (branch A, sub-topic A1).
- `wiki/raw/sessions/phase-0-a2-logic-gates.md` **extends** `wiki/raw/sessions/phase-0-a1-cmos.md` (A1 → A2 sequential).
- `wiki/raw/sessions/phase-0-a3-clock-timing.md` **extends** `wiki/raw/sessions/phase-0-a2-logic-gates.md` (A2 → A3 sequential).
- `wiki/raw/sessions/phase-0-a4-combinational-sequential.md` **extends** `wiki/raw/sessions/phase-0-a3-clock-timing.md` (A3 → A4 sequential).

Phase 0 sub-concepts:
- `wiki/raw/sessions/phase-0-a1-cmos.md` `MOSFET` concept **packages** `wiki/raw/sessions/phase-0-a1-cmos.md`.
- `wiki/raw/sessions/phase-0-a2-logic-gates.md` `NAND universal` concept **packages** `wiki/raw/sessions/phase-0-a2-logic-gates.md`.
- `wiki/raw/sessions/phase-0-a2-logic-gates.md` `logic gates` concept **packages** `wiki/raw/sessions/phase-0-a2-logic-gates.md`.
- `wiki/raw/sessions/phase-0-a3-clock-timing.md` `clock` concept **packages** `wiki/raw/sessions/phase-0-a3-clock-timing.md`.
- `wiki/raw/sessions/phase-0-a3-clock-timing.md` `skew & jitter` concept **packages** `wiki/raw/sessions/phase-0-a3-clock-timing.md`.
- `wiki/raw/sessions/phase-0-a3-clock-timing.md` `sync vs async` concept **packages** `wiki/raw/sessions/phase-0-a3-clock-timing.md`.
- `wiki/raw/sessions/phase-0-a4-combinational-sequential.md` `Moore vs Mealy FSM` concept **packages** `wiki/raw/sessions/phase-0-a4-combinational-sequential.md`.

## 7. README ↔ spec bridges

- `README.md` G0-G4 gate summary **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §8 gate-based execution.
- `README.md` project description **implements** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 project intent.

## 8. CDK Lambda handler ↔ WorkflowStack bridges

B6 WorkflowStack의 3 Lambda Python handler는 stack에서 `lambda.Function(..., code=Code.fromAsset('lambdas/...'))` 로 asset 참조되지만 tree-sitter-python ↔ tree-sitter-typescript 교차 AST edge는 graphify가 포착하지 못한다. 각 handler는 stack의 Lambda 리소스를 **implements**.

- `cdk/lambdas/validate-spec/index.py` **implements** `cdk/lib/stacks/WorkflowStack.ts` (ValidateSpec Lambda handler).
- `cdk/lambdas/init-generation/index.py` **implements** `cdk/lib/stacks/WorkflowStack.ts` (InitGeneration Lambda handler).
- `cdk/lambdas/finalize/index.py` **implements** `cdk/lib/stacks/WorkflowStack.ts` (Finalize Lambda handler).
- `cdk/lambdas/validate-spec/index.py` `RejectedNotInG1Scope` **grounds** `src/semi_design_runner/validator.py` (L1 spec §4.2 error taxonomy — Lambda · Python runner 동일 string-level 계약).

## 9. L2 spec ↔ L2 schema bridges

L2 derived spec (commit `98149de`) §5.2 output schema가 `src/semi_design_runner/l2_schema.py` 로 코드화. Python `from ... import L2RecallNode` 는 graphify AST가 포착하지만, spec doc ↔ code cross-trench는 명시 필요.

- `src/semi_design_runner/l2_schema.py` **implements** `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` §5.2 (L2RecallNode 9 optional 필드).
- `src/semi_design_runner/l2_schema.py` **implements** `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` §3.3 #5 (`confidence*` 격리 규칙 — 모듈 docstring으로 강제).
- `tests/runner/test_l2_schema.py` **tests** `src/semi_design_runner/l2_schema.py` (Pydantic round-trip · Literal validation · 격리 docstring 정적 assertion).
- `src/semi_design_runner/l2_schema.py` **grounds** `docs/superpowers/specs/2026-04-23-L2-substrate-codex-review.md` R1 fix #1 (`Optional[...] = None` 명시 default enforcement).

## 10. L2 runtime scripts ↔ L2 schema/spec bridges

Issue #7 (compute_confidence) · #8 (inject_freshness) — 두 script 모두 `L2RecallNode` 필드를 **produce** 하며 L2 derived spec의 §3.2 / §3.3 / §4 섹션을 구현한다. Python import는 AST가 포착하지만 spec doc ↔ code · Makefile target ↔ script는 cross-trench.

### 10.1 compute_confidence (Alternative B mapping)

- `src/semi_design_runner/confidence.py` **implements** `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` §3.2 (tier × source_count → GOLD/SILVER/BRONZE 매핑 표).
- `src/semi_design_runner/confidence.py` **implements** `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` §3.3 #4 (source identity 결측 chunk 제외 · GOLD cross-source 강제).
- `src/semi_design_runner/confidence.py` **grounds** `src/semi_design_runner/l2_schema.py` (L2RecallNode-compatible dict producer).
- `scripts/compute_confidence.py` **implements** `src/semi_design_runner/confidence.py` (wheel-packaged core의 thin CLI shim).
- `tests/runner/test_compute_confidence.py` **tests** `src/semi_design_runner/confidence.py` (12 assertion: §3.2 matrix · §3.3 #4 edge · reproducibility · CLI modes).
- `pyproject.toml` `[project.scripts] semi-confidence` **implements** `src/semi_design_runner/confidence_cli.py` (console script entry point).

### 10.2 inject_freshness (§4 A-MEM timestamp injection)

- `scripts/inject_freshness.py` **implements** `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` §4 (last_ingested · valid_from · valid_to idempotent injection).
- `scripts/inject_freshness.py` **grounds** `src/semi_design_runner/l2_schema.py` (freshness 3 필드의 유일한 producer — §4.2 `age_days` 는 derivable이라 non-writeback).
- `Makefile` `graph-update` + `freshness-inject` target **implements** `scripts/inject_freshness.py` (incremental rebuild chain).
- `tests/runner/test_inject_freshness.py` **tests** `scripts/inject_freshness.py` (10 assertion: fresh/reingest/manual-expire/idempotency/ISO-8601/multi-source mtime/missing source warning).
- `Makefile` `freshness-inject` **extends** `issues/005-graphify-refresh-and-integrity-policy.md` §1 (full rebuild cadence와 구분되는 incremental freshness layer).

## 11. Archived spec concept bridges

2026-04-17 archived spec의 개념들은 2026-04-19 integrated spec이 **supersedes**.

- `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` `Cross-LLM Consensus` **extends** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §4.3 H3 evaluator separation (동일 원칙의 이전 표현).
- `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` `HUGI (Hardware Unified Generation Interface)` **extends** `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` §1 seam 2 (executable memory의 이전 표현).

---

## 운영 원칙

- 본 manifest는 **최소-간섭** 원칙: graph extraction pipeline 자체를 수정하지 않고, Part B가 본 문서를 일반 doc으로 처리하며 자연스럽게 edges를 추출하게 한다.
- Rebuild 시 본 문서의 각 "A **relation** B" 문장이 새 edge가 된다. Duplicate edges는 graphify build에서 dedup.
- 본 manifest를 **authoritative로 삼지 말 것**. AST/Part B가 직접 발견하는 edges가 우선. 본 manifest는 gap-fill 용도.
- 본 manifest를 **정기 정제** 할 것 — AST/Part B가 다음 iteration에서 자연 발견한 edges는 manifest에서 제거해 중복 방지.
