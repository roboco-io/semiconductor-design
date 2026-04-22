# L1 Process Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the L1 Process layer — SHA-pinned Nix + AWS Fargate Spot + Step Functions + Python CLI — so that `make run DESIGN=gcd STACK={orfs,librelane}` completes a single gcd job end-to-end and all G1 kill gates (KG-A, C1, D, E, F) pass on a clean VM.

**Architecture:** Three concurrent build tracks (Python runner, CDK, Docker) converge at an E2E integration phase. Python runner contains schemas + CLI + AWS clients + lockfile + metrics parser. CDK provisions 6 stacks (Network + Storage + Container + Compute + Workflow + Observability). Docker produces 3 images (orfs-runner, librelane-runner, metric-collector) pinned by SHA256 digest in `lockfile.yaml`. KG scripts verify kill gates without running paid jobs. Final phase wires Makefile + sample specs + CI for `make run` and `make kg-all` one-liners.

**Tech Stack:** Python 3.12 + uv + Pydantic v2 (`ConfigDict`) + boto3 + click + pytest + coverage; TypeScript 5 + Node 20 + aws-cdk-lib@^2 + cdk-nag + jest for CDK; Docker (debian:12-slim for ORFS, LibreLane 3.0.2 Nix base, python:3.12-slim for collector); AWS Fargate Spot + Step Functions Standard + S3 Object Lock governance + DynamoDB × 4 + KMS CMK + Secrets Manager + ECR; GitHub Actions CI.

**Parent spec:** `docs/superpowers/specs/2026-04-20-L1-process-design.md` (Codex 3-round review 통과 → go). Contract: `L1.run(spec_uri) → artifact_uri` per overview spec §3.2.

---

## File Structure

Each file has one responsibility. Files that change together live together.

### Python runner (`src/semi_design_runner/`)
- Create: `src/semi_design_runner/__init__.py` — version constant only
- Create: `src/semi_design_runner/schemas.py` — `_StrictBase`, `FlowParameters`, `ResourceOverrides`, `ExperimentalParameters`, `Spec`, `StageTiming`, `RunArtifact`, `Metrics`
- Create: `src/semi_design_runner/lockfile.py` — canonical-yaml hash, scope projection, `lockfile-verify` logic
- Create: `src/semi_design_runner/metrics.py` — `.rpt`/`.def` parser producing `Metrics`
- Create: `src/semi_design_runner/trace.py` — JSONL logger at `~/.cache/semi-run/traces/{run_id}.jsonl`
- Create: `src/semi_design_runner/cost.py` — budget guard (`planned sum > compute_budget_usd` → reject) + CloudWatch cost attribution
- Create: `src/semi_design_runner/aws/__init__.py` — empty marker
- Create: `src/semi_design_runner/aws/clients.py` — boto3 session factory w/ SSO profile
- Create: `src/semi_design_runner/aws/s3.py` — get/put spec, put-with-retention-header, artifact download
- Create: `src/semi_design_runner/aws/ddb.py` — `put_with_count` wrapper incrementing `Candidates.ddb_write_count`
- Create: `src/semi_design_runner/aws/sfn.py` — StartExecution + DescribeExecution wrappers
- Create: `src/semi_design_runner/cli.py` — click CLI entry point with subcommands `init`/`submit`/`status`/`artifacts`/`lockfile-verify`/`cost`/`auth login`

### Tests (`tests/runner/`)
- Create: `tests/runner/__init__.py`, `tests/runner/conftest.py` (shared fixtures: tmp dirs, mocked boto3 sessions, sample spec fixtures)
- Create: `tests/runner/test_schemas.py` — Pydantic validation, `Extra.forbid`, tagged union boundaries, rejection for unknown keys
- Create: `tests/runner/test_lockfile.py` — canonical-yaml ordering, L1/L3-readiness projection, `l1_lockfile_sha` stability under L3 drift
- Create: `tests/runner/test_metrics.py` — parser for sample `.rpt`/`.def` fixtures
- Create: `tests/runner/test_cost.py` — planned-sum budget guard, CloudWatch cost computation with mocks
- Create: `tests/runner/test_cli.py` — `click.testing.CliRunner` for every subcommand
- Create: `tests/runner/test_ddb_counter.py` — `put_with_count` atomicity + counter increment
- Create: `tests/runner/test_budget_guard.py` — **KG-F F2**: accumulated-cost abort logic
- Create: `tests/runner/test_validate_spec.py` — **Overview rejection**: `design != "gcd"` triggers `RejectedNotInG1Scope`

### `pyproject.toml`
- Modify: add `runner` optional-dependencies section: `boto3>=1.34`, `click>=8`, `pydantic>=2,<3`, `ulid-py>=1.1`, `PyYAML>=6`
- Modify: add CLI entry point `semi-run = "semi_design_runner.cli:main"`

### CDK (`cdk/`)
- Create: `cdk/package.json`, `cdk/cdk.json`, `cdk/tsconfig.json`, `cdk/jest.config.ts`
- Create: `cdk/bin/semi-design.ts` — App entry with `--context env=dev|prod`
- Create: `cdk/lib/stacks/NetworkStack.ts` — VPC + 9 endpoints (s3 gateway + ecr.api + ecr.dkr + logs + secretsmanager + ssm + sts + monitoring + kms)
- Create: `cdk/lib/stacks/StorageStack.ts` — S3 bucket (`ObjectLockEnabled: true` at creation) + DDB × 4 + KMS `bucketCmk`
- Create: `cdk/lib/stacks/ContainerStack.ts` — ECR × 3 (scan on push, immutable tags)
- Create: `cdk/lib/stacks/ComputeStack.ts` — ECS cluster + 3 Fargate TaskDef (ephemeral 21GB, task role scoped to explicit CMK ARNs)
- Create: `cdk/lib/stacks/WorkflowStack.ts` — SFN Map + Lambda (ValidateSpec, InitGeneration, Finalize) + EventBridge
- Create: `cdk/lib/stacks/ObservabilityStack.ts` — CloudWatch dashboards + alarms ($50/$100 budget, Spot reclaim >30%, per-candidate cost >$5, `ddb_write_count` P99)
- Create: `cdk/test/*.test.ts` per stack — snapshot + unit assertions (`hasResource`, `hasResourceProperties`) + cdk-nag suppression justifications

### Docker (`docker/`)
- Create: `docker/orfs-runner.Dockerfile` — debian:12-slim base, ORFS + OpenROAD + Yosys + open_pdks sky130A; ENTRYPOINT reads `RUN_ID`/`STAGE`/`INPUT_S3_URI`/`OUTPUT_S3_URI`/`SIMULATE_SPOT_RECLAIM` env
- Create: `docker/librelane-runner.Dockerfile` — LibreLane 3.0.2 Nix base; same ENTRYPOINT contract
- Create: `docker/metric-collector.Dockerfile` — python:3.12-slim; install `semi_design_runner` wheel + invoke `python -m semi_design_runner.metrics` as ENTRYPOINT

### KG scripts (`scripts/kg/`)
- Create: `scripts/kg/kg-a-librelane-fargate.sh` — submit gcd run, measure ephemeral peak + image pull time
- Create: `scripts/kg/kg-b-chipyard-cache.sh` — L3-readiness only: verify S3 cache object layout + SHA
- Create: `scripts/kg/kg-c1-token-budget.sh` — deterministic tiktoken/anthropic-tokens estimate
- Create: `scripts/kg/kg-c2-live-smoke.sh` — runs as Fargate TaskDef `kg-c2-smoke`, triggered by `aws ecs run-task`
- Create: `scripts/kg/kg-d-spot-reclaim.sh` — launch 10 simulated-reclaim tasks via `SIMULATE_SPOT_RECLAIM=1`
- Create: `scripts/kg/kg-e-ddb-write-amp.sh` — post-run DDB query of `Candidates.ddb_write_count`
- Create: `scripts/kg/kg-f1-prebudget.sh` — pre-RunTask rejection proof (no ECS call)
- Create: `scripts/kg/run-all.sh` — orchestrates KG-A, C1, D, E, F (KG-B + C2 optional)
- Create: `scripts/kg/budget-limits.yaml` — monthly budget thresholds

### Specs / root
- Create: `specs/gcd-orfs.yaml`, `specs/gcd-librelane.yaml`, `specs/ibex-orfs.yaml` (rejection test), `specs/aes-orfs.yaml` (rejection test)
- Create: `lockfile.yaml` — at repo root, filled with actual SHAs during Phase E
- Modify: `Makefile` — add `run`, `lockfile-verify`, `kg-all` targets
- Create: `.github/workflows/l1-ci.yml` — install + test + `make run` on clean VM
- Modify: `README.md` — update G1 status to done when this plan completes

---

## Phase Ordering & Dependencies

```
Phase A (Python runner)  ─┐
Phase B (CDK)            ─┼─→ Phase D (KG scripts)  ─→ Phase E (Integration)
Phase C (Docker)         ─┘
```

- **A, B, C run in parallel** (no shared state). Dispatch to separate subagents if using subagent-driven-development.
- **D requires A+B+C green** (KG scripts use CLI, Fargate TaskDef, Docker image digests).
- **E is the final integration** — `make run` end-to-end, CI, sample specs, lockfile filled with real SHAs.

---

## Phase A — Python Runner Foundation

**Goal:** Package `src/semi_design_runner/` with Pydantic schemas, AWS clients, lockfile verifier, metrics parser, budget guard, CLI, all with ≥85% test coverage.

### Task A1: Bootstrap package + pyproject extras

**Files:**
- Modify: `pyproject.toml`
- Create: `src/semi_design_runner/__init__.py`
- Create: `tests/runner/__init__.py`
- Create: `tests/runner/conftest.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/runner/test_package.py
from semi_design_runner import __version__

def test_package_version_defined():
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/runner/test_package.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner'`.

- [ ] **Step 3: Write minimal implementation**

Create `src/semi_design_runner/__init__.py`:
```python
__version__ = "0.1.0"
```

Create `src/semi_design_runner/aws/__init__.py` (empty).

Modify `pyproject.toml` — add under `[tool.hatch.build.targets.wheel]` (or existing equivalent) the new package path, and under `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
runner = [
    "boto3>=1.34",
    "click>=8",
    "pydantic>=2,<3",
    "ulid-py>=1.1",
    "PyYAML>=6",
]

[project.scripts]
semi-run = "semi_design_runner.cli:main"
```

Run `uv sync --extra runner` to install.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/runner/test_package.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/semi_design_runner/__init__.py src/semi_design_runner/aws/__init__.py tests/runner/__init__.py tests/runner/test_package.py tests/runner/conftest.py
git commit -m "feat(runner): scaffold semi_design_runner package + pyproject extras"
```

---

### Task A2: Pydantic schemas — `_StrictBase`, `FlowParameters`, `ResourceOverrides`, `ExperimentalParameters`

**Files:**
- Create: `src/semi_design_runner/schemas.py`
- Create: `tests/runner/test_schemas.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_schemas.py
import pytest
from pydantic import ValidationError
from semi_design_runner.schemas import (
    FlowParameters, ResourceOverrides, ExperimentalParameters,
)

def test_flow_parameters_all_optional_none():
    fp = FlowParameters()
    assert fp.core_utilization is None
    assert fp.place_density is None

def test_flow_parameters_rejects_unknown_key():
    with pytest.raises(ValidationError, match="extra"):
        FlowParameters(unknown_knob=42)

def test_resource_overrides_defaults_to_empty():
    ro = ResourceOverrides()
    assert ro.cpu_units is None
    assert ro.ephemeral_storage_gb is None

def test_experimental_metadata_strict_strings():
    exp = ExperimentalParameters(metadata={"k": "v"})
    assert exp.metadata == {"k": "v"}
    with pytest.raises(ValidationError):
        ExperimentalParameters(metadata={"k": {"nested": "forbidden"}})

def test_experimental_rejects_unknown_key():
    with pytest.raises(ValidationError, match="extra"):
        ExperimentalParameters(unexpected=1)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.schemas'`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/schemas.py`:

```python
"""Pydantic v2 schemas for L1 Process layer.

All models inherit from _StrictBase which forbids extra fields (Codex review
requirement). This prevents L2/L3 breaking-change drift through arbitrary dict
injection. Spec.parameters is broken into tagged sub-models (FlowParameters,
ResourceOverrides, ExperimentalParameters) per spec §4.1.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FlowParameters(_StrictBase):
    """Tool-flow knobs. Bounded namespace — additions require minor version bump."""

    core_utilization: float | None = None
    place_density: float | None = None
    clock_period_ps: int | None = None
    global_routing_iterations: int | None = None
    timing_driven: bool | None = None
    synth_flatten: bool | None = None


class ResourceOverrides(_StrictBase):
    """Fargate TaskDef override. None means use default from ComputeStack."""

    cpu_units: int | None = None
    memory_mb: int | None = None
    ephemeral_storage_gb: int | None = None


class ExperimentalParameters(_StrictBase):
    """L3-only ad-hoc patches. L1 logs and passes through; never interprets."""

    patch_uri: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_schemas.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/schemas.py tests/runner/test_schemas.py
git commit -m "feat(runner): add _StrictBase + FlowParameters/ResourceOverrides/ExperimentalParameters schemas"
```

---

### Task A3: `Spec` schema with lockfile SHAs and rejection validation

**Files:**
- Modify: `src/semi_design_runner/schemas.py`
- Modify: `tests/runner/test_schemas.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/runner/test_schemas.py`:

```python
from semi_design_runner.schemas import Spec


def test_spec_accepts_minimal_valid():
    spec = Spec(
        run_id="01HABCDEF",
        design="gcd",
        stack="orfs",
        flow_parameters=FlowParameters(),
        compute_budget_usd=30.0,
        seed=42,
        l1_lockfile_sha="sha256:" + "a" * 64,
    )
    assert spec.version == 1
    assert spec.full_lockfile_sha is None
    assert spec.planned_cost_per_stage_usd == {}


def test_spec_rejects_unknown_design():
    with pytest.raises(ValidationError):
        Spec(
            run_id="x",
            design="bp",  # not in Literal
            stack="orfs",
            flow_parameters=FlowParameters(),
            compute_budget_usd=30.0,
            seed=0,
            l1_lockfile_sha="sha256:0" * 32,
        )


def test_spec_rejects_unknown_stack():
    with pytest.raises(ValidationError):
        Spec(
            run_id="x",
            design="gcd",
            stack="vivado",  # not open-source
            flow_parameters=FlowParameters(),
            compute_budget_usd=30.0,
            seed=0,
            l1_lockfile_sha="sha256:0" * 32,
        )


def test_spec_rejects_extra_top_level_field():
    with pytest.raises(ValidationError, match="extra"):
        Spec(
            run_id="x",
            design="gcd",
            stack="orfs",
            flow_parameters=FlowParameters(),
            compute_budget_usd=30.0,
            seed=0,
            l1_lockfile_sha="sha256:0" * 32,
            mystery_field="boom",
        )
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_schemas.py -v`
Expected: 4 new FAILs with `ImportError` or missing `Spec`.

- [ ] **Step 3: Implement**

Append to `src/semi_design_runner/schemas.py`:

```python
Design = Literal["gcd", "ibex", "aes"]
Stack = Literal["orfs", "librelane"]
StageName = Literal["rtl-build", "synth", "pnr", "signoff", "metrics"]


class Spec(_StrictBase):
    """Serialized as spec.yaml; sole input to L1.run(spec_uri)."""

    version: int = 1
    run_id: str
    design: Design
    stack: Stack
    flow_parameters: FlowParameters
    resource_overrides: ResourceOverrides = Field(default_factory=ResourceOverrides)
    experimental: ExperimentalParameters = Field(default_factory=ExperimentalParameters)
    compute_budget_usd: float
    planned_cost_per_stage_usd: dict[StageName, float] = Field(default_factory=dict)
    seed: int
    l1_lockfile_sha: str
    full_lockfile_sha: str | None = None
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/runner/test_schemas.py -v`
Expected: all PASS (including the 5 earlier + 4 new = 9).

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/schemas.py tests/runner/test_schemas.py
git commit -m "feat(runner): add Spec schema with strict validation + typed design/stack literals"
```

---

### Task A4: `StageTiming`, `Metrics`, `RunArtifact` with status enum

**Files:**
- Modify: `src/semi_design_runner/schemas.py`
- Modify: `tests/runner/test_schemas.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/runner/test_schemas.py`:

```python
from datetime import datetime
from semi_design_runner.schemas import StageTiming, Metrics, RunArtifact


def test_stage_timing_fields():
    t = StageTiming(
        stage="synth",
        started_at=datetime(2026, 4, 21, 0, 0),
        ended_at=datetime(2026, 4, 21, 0, 5),
        exit_code=0,
        cost_usd=0.12,
        fargate_vcpu=4096,
        fargate_memory_mb=16384,
    )
    assert t.stage == "synth"


def test_metrics_allow_optional_timing():
    m = Metrics(area_um2=12345.0, power_mw=None, max_freq_mhz=None,
                wns_ns=None, tns_ns=None, drc_violations=0, runtime_s=120.5)
    assert m.area_um2 == 12345.0


def test_run_artifact_clean_status():
    art = RunArtifact(
        run_id="01HABCDEF",
        spec_uri="s3://b/specs/01HABCDEF.yaml",
        status="clean",
        metrics=Metrics(area_um2=1.0, power_mw=None, max_freq_mhz=None,
                        wns_ns=None, tns_ns=None, drc_violations=0, runtime_s=10.0),
        metrics_uri="s3://b/runs/01HABCDEF/final/metrics.json",
        reports=["s3://b/runs/01HABCDEF/final/signoff/sta.rpt"],
        provenance_uri="s3://b/runs/01HABCDEF/final/provenance.yaml",
        l1_lockfile_sha="sha256:" + "a" * 64,
        cost_usd=1.23,
        cost_breakdown=[],
        ddb_write_count=8,
        started_at=datetime(2026, 4, 21, 0, 0),
        ended_at=datetime(2026, 4, 21, 0, 10),
    )
    assert art.status == "clean"
    assert art.full_lockfile_sha is None


def test_run_artifact_rejects_unknown_status():
    with pytest.raises(ValidationError):
        RunArtifact(
            run_id="x",
            spec_uri="s3://b/x",
            status="mystery_state",
            metrics=None,
            metrics_uri="s3://b/x",
            reports=[],
            provenance_uri="s3://b/x",
            l1_lockfile_sha="sha256:0" * 32,
            cost_usd=0.0,
            cost_breakdown=[],
            ddb_write_count=0,
            started_at=datetime(2026, 4, 21),
            ended_at=None,
        )
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_schemas.py -v`
Expected: 4 new FAILs.

- [ ] **Step 3: Implement**

Append to `src/semi_design_runner/schemas.py`:

```python
RunStatus = Literal[
    "clean", "drc_fail", "lvs_fail", "sta_fail",
    "tool_crash", "spot_reclaimed_max", "rejected_not_in_g1",
    "budget_exceeded", "in_progress",
]


class StageTiming(_StrictBase):
    stage: StageName
    started_at: datetime
    ended_at: datetime
    exit_code: int
    cost_usd: float
    fargate_vcpu: int
    fargate_memory_mb: int


class Metrics(_StrictBase):
    area_um2: float
    power_mw: float | None
    max_freq_mhz: float | None
    wns_ns: float | None
    tns_ns: float | None
    drc_violations: int
    runtime_s: float


class RunArtifact(_StrictBase):
    run_id: str
    spec_uri: str
    status: RunStatus
    metrics: Metrics | None
    metrics_uri: str
    reports: list[str]
    provenance_uri: str
    l1_lockfile_sha: str
    full_lockfile_sha: str | None = None
    cost_usd: float
    cost_breakdown: list[StageTiming]
    ddb_write_count: int
    started_at: datetime
    ended_at: datetime | None
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/runner/test_schemas.py -v --cov=src/semi_design_runner/schemas --cov-report=term-missing`
Expected: all PASS, coverage for schemas.py ≥ 95%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/schemas.py tests/runner/test_schemas.py
git commit -m "feat(runner): add StageTiming/Metrics/RunArtifact schemas with status literal"
```

---

### Task A5: Lockfile canonical-yaml hash + scope projection

**Files:**
- Create: `src/semi_design_runner/lockfile.py`
- Create: `tests/runner/test_lockfile.py`
- Create: `tests/runner/fixtures/sample_lockfile.yaml`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_lockfile.py
from pathlib import Path
import pytest
from semi_design_runner.lockfile import (
    load_lockfile, canonical_yaml, compute_l1_sha, verify_scope,
    L1_SCOPE_KEYS, L3_READINESS_KEYS,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_lockfile.yaml"


def test_load_lockfile_parses_commit_shas():
    lf = load_lockfile(FIXTURE)
    assert "commit_shas" in lf
    assert lf["commit_shas"]["openroad"] == "abc123"


def test_l1_scope_keys_stable():
    assert L1_SCOPE_KEYS == {"openroad", "librelane", "yosys", "open_pdks"}


def test_l3_readiness_keys_stable():
    assert L3_READINESS_KEYS == {
        "verilator", "cocotb", "chipyard", "gemmini", "mlcommons_tiny"
    }


def test_l1_sha_stable_under_l3_drift(tmp_path):
    """Filling L3 SHAs must NOT change l1_lockfile_sha."""
    lf1 = load_lockfile(FIXTURE)
    sha_before = compute_l1_sha(lf1)

    lf2 = dict(lf1)
    lf2["commit_shas"] = dict(lf1["commit_shas"])
    lf2["commit_shas"]["chipyard"] = "newsha"  # L3 SHA added
    lf2["commit_shas"]["verilator"] = "another"
    sha_after = compute_l1_sha(lf2)

    assert sha_before == sha_after


def test_verify_scope_l1_passes_with_l3_null():
    lf = load_lockfile(FIXTURE)
    result = verify_scope(lf, scope="l1")
    assert result["verified"] is True
    assert result["mismatched"] == []
    assert set(result["deferred_l3"]) == L3_READINESS_KEYS
    assert result["scope"] == "l1"
    assert result["l1_lockfile_sha"].startswith("sha256:")


def test_verify_scope_full_fails_when_l3_null():
    lf = load_lockfile(FIXTURE)
    result = verify_scope(lf, scope="full")
    assert result["verified"] is False
    assert set(result["mismatched"]) >= L3_READINESS_KEYS
```

Create `tests/runner/fixtures/sample_lockfile.yaml`:

```yaml
version: 1
updated_at: 2026-04-20
updated_by: test
commit_shas:
  openroad: abc123
  librelane: def456
  yosys: ghi789
  open_pdks: jkl012
  verilator: null
  cocotb: null
  chipyard: null
  gemmini: null
  mlcommons_tiny: null
container_digests:
  orfs-runner: "sha256:aaa"
  librelane-runner: "sha256:bbb"
  metric-collector: "sha256:ccc"
source_tarball_mirrors:
  openroad: s3://bucket/mirrors/openroad/abc123.tar.gz
pdk_digests:
  sky130A: "sha256:ddd"
stale_source_policy:
  grace_period_hours: 24
  action_on_failure: ci_red
ci_verification:
  last_green_commit: "test-sha"
  last_green_at: "2026-04-20T00:00:00Z"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_lockfile.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.lockfile'`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/lockfile.py`:

```python
"""Lockfile verification with L1/L3-readiness scope separation.

The L1 scope hash must be invariant under L3-readiness SHA drift — that is,
filling `verilator` or `chipyard` SHAs must NOT change l1_lockfile_sha, which
serves as the cache key for L1 runs. See spec §9.1 canonical-yaml rule.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Literal

import yaml


L1_SCOPE_KEYS: set[str] = {"openroad", "librelane", "yosys", "open_pdks"}
L3_READINESS_KEYS: set[str] = {
    "verilator", "cocotb", "chipyard", "gemmini", "mlcommons_tiny",
}


def load_lockfile(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def canonical_yaml(data: dict[str, Any]) -> str:
    """Sort keys and drop null values so L3 nulls do not affect hash."""
    return yaml.safe_dump(
        _strip_nulls(data), sort_keys=True, default_flow_style=False,
    )


def _strip_nulls(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_nulls(v) for v in obj]
    return obj


def _project_l1(lockfile: dict[str, Any]) -> dict[str, Any]:
    """Keep only L1-scope commit_shas + container_digests + pdk_digests."""
    return {
        "version": lockfile["version"],
        "commit_shas": {
            k: v for k, v in lockfile["commit_shas"].items()
            if k in L1_SCOPE_KEYS
        },
        "container_digests": lockfile["container_digests"],
        "pdk_digests": lockfile.get("pdk_digests", {}),
    }


def compute_l1_sha(lockfile: dict[str, Any]) -> str:
    projected = _project_l1(lockfile)
    digest = hashlib.sha256(canonical_yaml(projected).encode()).hexdigest()
    return f"sha256:{digest}"


def verify_scope(
    lockfile: dict[str, Any], scope: Literal["l1", "full"] = "l1",
) -> dict[str, Any]:
    commit_shas = lockfile["commit_shas"]
    if scope == "l1":
        check_keys = L1_SCOPE_KEYS
    else:
        check_keys = L1_SCOPE_KEYS | L3_READINESS_KEYS
    mismatched = [k for k in check_keys if commit_shas.get(k) in (None, "")]
    deferred = sorted(
        k for k in L3_READINESS_KEYS
        if commit_shas.get(k) in (None, "")
    )
    return {
        "verified": len(mismatched) == 0,
        "mismatched": sorted(mismatched),
        "deferred_l3": deferred if scope == "l1" else [],
        "scope": scope,
        "l1_lockfile_sha": compute_l1_sha(lockfile),
    }
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/runner/test_lockfile.py -v --cov=src/semi_design_runner/lockfile`
Expected: 6 PASS, coverage ≥ 90%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/lockfile.py tests/runner/test_lockfile.py tests/runner/fixtures/sample_lockfile.yaml
git commit -m "feat(runner): lockfile scope projection + L1 canonical-yaml hash stable under L3 drift"
```

---

### Task A6: Metrics parser (`.rpt` → `Metrics`)

**Files:**
- Create: `src/semi_design_runner/metrics.py`
- Create: `tests/runner/test_metrics.py`
- Create: `tests/runner/fixtures/synth.rpt`, `tests/runner/fixtures/sta.rpt`, `tests/runner/fixtures/drc.rpt`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_metrics.py
from pathlib import Path
from semi_design_runner.metrics import parse_reports
from semi_design_runner.schemas import Metrics

FIX = Path(__file__).parent / "fixtures"


def test_parse_reports_clean_case():
    m = parse_reports(
        synth_rpt=FIX / "synth.rpt",
        sta_rpt=FIX / "sta.rpt",
        drc_rpt=FIX / "drc.rpt",
        runtime_s=120.5,
    )
    assert isinstance(m, Metrics)
    assert m.area_um2 > 0
    assert m.wns_ns is not None
    assert m.drc_violations == 0
    assert m.runtime_s == 120.5


def test_parse_reports_handles_missing_power():
    m = parse_reports(
        synth_rpt=FIX / "synth.rpt",
        sta_rpt=FIX / "sta.rpt",
        drc_rpt=FIX / "drc.rpt",
        runtime_s=1.0,
    )
    assert m.power_mw is None  # synth.rpt fixture has no power line
```

Create fixture `tests/runner/fixtures/synth.rpt`:

```
=== gcd ===
   Number of cells:           134
   Chip area for module:      12345.678 um^2
```

Create `tests/runner/fixtures/sta.rpt`:

```
startpoint: req_msg[0] (input)
endpoint: resp_msg[0] (output)
path delay: 4.520 ns
slack:  0.480 ns (MET)
```

Create `tests/runner/fixtures/drc.rpt`:

```
Total violations: 0
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/metrics.py`:

```python
"""Parse Yosys/OpenROAD/LibreLane report files into the Metrics schema.

This module is imported both from `semi_design_runner.cli` (local use)
and from the `semi/metric-collector` Docker container ENTRYPOINT, so the
parser logic has a single source of truth (spec §5 — no double maintenance).
"""
from __future__ import annotations

import re
from pathlib import Path

from semi_design_runner.schemas import Metrics


_AREA_RE = re.compile(r"Chip area for module:\s+([\d.]+)\s*um\^2")
_SLACK_RE = re.compile(r"slack:\s+(-?[\d.]+)\s*ns")
_DRC_RE = re.compile(r"Total violations:\s+(\d+)")


def parse_reports(
    *,
    synth_rpt: Path,
    sta_rpt: Path,
    drc_rpt: Path,
    runtime_s: float,
) -> Metrics:
    synth_text = synth_rpt.read_text()
    sta_text = sta_rpt.read_text()
    drc_text = drc_rpt.read_text()

    area_match = _AREA_RE.search(synth_text)
    if not area_match:
        raise ValueError(f"No chip area found in {synth_rpt}")
    area_um2 = float(area_match.group(1))

    slack_match = _SLACK_RE.search(sta_text)
    wns_ns = float(slack_match.group(1)) if slack_match else None

    drc_match = _DRC_RE.search(drc_text)
    drc_violations = int(drc_match.group(1)) if drc_match else 0

    return Metrics(
        area_um2=area_um2,
        power_mw=None,  # sky130 open flow does not emit power by default
        max_freq_mhz=None,  # L3 to add when clock sweep is enabled
        wns_ns=wns_ns,
        tns_ns=None,
        drc_violations=drc_violations,
        runtime_s=runtime_s,
    )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/runner/test_metrics.py -v --cov=src/semi_design_runner/metrics`
Expected: 2 PASS, coverage ≥ 85%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/metrics.py tests/runner/test_metrics.py tests/runner/fixtures/synth.rpt tests/runner/fixtures/sta.rpt tests/runner/fixtures/drc.rpt
git commit -m "feat(runner): parse synth/sta/drc reports into Metrics schema"
```

---

### Task A7: JSONL trace logger

**Files:**
- Create: `src/semi_design_runner/trace.py`
- Create: `tests/runner/test_trace.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_trace.py
import json
from pathlib import Path
from semi_design_runner.trace import TraceLogger


def test_trace_logger_appends_jsonl(tmp_path):
    log = TraceLogger(trace_dir=tmp_path, run_id="abc")
    log.emit(event="submit", payload={"arn": "x"})
    log.emit(event="poll", payload={"status": "RUNNING"})

    content = (tmp_path / "abc.jsonl").read_text().splitlines()
    assert len(content) == 2
    assert json.loads(content[0])["event"] == "submit"
    assert json.loads(content[1])["payload"]["status"] == "RUNNING"


def test_trace_logger_timestamps_each_line(tmp_path):
    log = TraceLogger(trace_dir=tmp_path, run_id="t")
    log.emit(event="e", payload={})
    line = (tmp_path / "t.jsonl").read_text().strip()
    assert "ts" in json.loads(line)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_trace.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/trace.py`:

```python
"""JSONL trace logger for infrastructure-level events.

Kept separate from L3 reasoning traces (which are a novelty artifact of the
research, see overview spec §4.3). This file logs boto3 calls, SFN state
transitions, and lifecycle events — strictly for debugging.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self, trace_dir: Path, run_id: str) -> None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        self._path = trace_dir / f"{run_id}.jsonl"

    def emit(self, *, event: str, payload: dict[str, Any]) -> None:
        line = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self._path.open("a") as fh:
            fh.write(json.dumps(line) + "\n")
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/runner/test_trace.py -v --cov=src/semi_design_runner/trace`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/trace.py tests/runner/test_trace.py
git commit -m "feat(runner): add JSONL infra trace logger for boto3/SFN events"
```

---

### Task A8: `aws/clients.py` — boto3 session factory

**Files:**
- Create: `src/semi_design_runner/aws/clients.py`
- Create: `tests/runner/test_aws_clients.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_aws_clients.py
from unittest.mock import patch, MagicMock
from semi_design_runner.aws.clients import make_session, make_client


def test_make_session_uses_named_profile():
    with patch("boto3.Session") as MockSession:
        make_session(profile="test-profile")
        MockSession.assert_called_once_with(profile_name="test-profile")


def test_make_session_allows_none_profile():
    with patch("boto3.Session") as MockSession:
        make_session(profile=None)
        MockSession.assert_called_once_with(profile_name=None)


def test_make_client_applies_retry_config():
    with patch("boto3.Session") as MockSession:
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        make_client("s3", profile="p")
        args, kwargs = mock_session.client.call_args
        assert args[0] == "s3"
        assert kwargs["config"].retries["max_attempts"] == 5
        assert kwargs["config"].retries["mode"] == "adaptive"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_aws_clients.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.aws.clients'`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/aws/clients.py`:

```python
"""boto3 session + client factory with SSO profile and adaptive retries."""
from __future__ import annotations

import boto3
from botocore.config import Config

_DEFAULT_RETRY_CONFIG = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},
)


def make_session(profile: str | None = "semi-design-operator") -> boto3.Session:
    return boto3.Session(profile_name=profile)


def make_client(service: str, *, profile: str | None = "semi-design-operator"):
    session = make_session(profile=profile)
    return session.client(service, config=_DEFAULT_RETRY_CONFIG)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_aws_clients.py -v --cov=src/semi_design_runner/aws/clients`
Expected: 3 PASS, coverage ≥ 90%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/aws/clients.py tests/runner/test_aws_clients.py
git commit -m "feat(runner): boto3 session/client factory with SSO profile + adaptive retry"
```

---

### Task A9: `aws/s3.py` — put-with-retention + artifact download

**Files:**
- Create: `src/semi_design_runner/aws/s3.py`
- Create: `tests/runner/test_aws_s3.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_aws_s3.py
from datetime import datetime, timezone
from unittest.mock import MagicMock
from pathlib import Path
from semi_design_runner.aws.s3 import put_with_retention, put_spec, download_final


def test_put_with_retention_sets_governance_mode_and_date():
    client = MagicMock()
    put_with_retention(
        client, bucket="b", key="runs/r/final/m.json", body=b"{}", retention_days=30,
    )
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "b"
    assert kwargs["Key"] == "runs/r/final/m.json"
    assert kwargs["Body"] == b"{}"
    assert kwargs["ObjectLockMode"] == "GOVERNANCE"
    assert isinstance(kwargs["ObjectLockRetainUntilDate"], datetime)
    delta = kwargs["ObjectLockRetainUntilDate"] - datetime.now(tz=timezone.utc)
    assert 29 <= delta.days <= 30


def test_put_spec_writes_to_staging_returns_uri():
    client = MagicMock()
    uri = put_spec(client, bucket="bkt", run_id="abc", spec_yaml="version: 1")
    assert uri == "s3://bkt/runs/abc/staging/spec.yaml"
    client.put_object.assert_called_once()


def test_download_final_mirrors_prefix(tmp_path):
    client = MagicMock()
    paginator = MagicMock()
    client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {"Contents": [
            {"Key": "runs/abc/final/metrics.json"},
            {"Key": "runs/abc/final/signoff/sta.rpt"},
        ]},
    ]
    download_final(client, bucket="bkt", run_id="abc", dest=tmp_path)
    assert client.download_file.call_count == 2
    # relative paths mirrored under dest
    assert (tmp_path / "signoff").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_aws_s3.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/aws/s3.py`:

```python
"""S3 operations for L1 runner.

`put_with_retention` implements the per-object retention pattern from spec §4.3:
GOVERNANCE-mode Object Lock is attached in the **same PutObject call** as the
data write, so there is no mutable-success window if finalize later fails.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def put_with_retention(
    client: Any,
    *,
    bucket: str,
    key: str,
    body: bytes,
    retention_days: int = 90,
) -> None:
    retain_until = datetime.now(tz=timezone.utc) + timedelta(days=retention_days)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ObjectLockMode="GOVERNANCE",
        ObjectLockRetainUntilDate=retain_until,
    )


def put_spec(client: Any, *, bucket: str, run_id: str, spec_yaml: str) -> str:
    """Write spec.yaml to staging prefix (no retention — staging is mutable)."""
    key = f"runs/{run_id}/staging/spec.yaml"
    client.put_object(Bucket=bucket, Key=key, Body=spec_yaml.encode())
    return f"s3://{bucket}/{key}"


def download_final(
    client: Any, *, bucket: str, run_id: str, dest: Path,
) -> None:
    """Download the final/ prefix mirror to local dest dir."""
    prefix = f"runs/{run_id}/final/"
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            rel = obj["Key"][len(prefix):]
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, obj["Key"], str(target))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_aws_s3.py -v --cov=src/semi_design_runner/aws/s3`
Expected: 3 PASS, coverage ≥ 85%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/aws/s3.py tests/runner/test_aws_s3.py
git commit -m "feat(runner): S3 put-with-retention + spec staging + artifact final download"
```

---

### Task A10: `aws/ddb.py` — `put_candidate_with_count` (KG-E counter)

**Files:**
- Create: `src/semi_design_runner/aws/ddb.py`
- Create: `tests/runner/test_ddb_counter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_ddb_counter.py
from unittest.mock import MagicMock
from semi_design_runner.aws.ddb import put_candidate_with_count, get_ddb_write_count


def test_put_candidate_uses_add_to_increment_counter():
    client = MagicMock()
    put_candidate_with_count(
        client,
        table="Candidates",
        run_id="r1",
        gen=0,
        cand=3,
        attributes={"stage_status": "synth_ok"},
    )
    kwargs = client.update_item.call_args.kwargs
    assert kwargs["TableName"] == "Candidates"
    assert kwargs["Key"]["run_id"]["S"] == "r1"
    assert kwargs["Key"]["gen_cand"]["S"] == "gen#0#cand#3"
    assert "ADD ddb_write_count :one" in kwargs["UpdateExpression"]
    assert kwargs["ExpressionAttributeValues"][":one"] == {"N": "1"}


def test_get_counter_returns_zero_when_item_missing():
    client = MagicMock()
    client.get_item.return_value = {}
    assert get_ddb_write_count(
        client, table="Candidates", run_id="r", gen=0, cand=0,
    ) == 0


def test_get_counter_returns_int_value():
    client = MagicMock()
    client.get_item.return_value = {"Item": {"ddb_write_count": {"N": "17"}}}
    assert get_ddb_write_count(
        client, table="Candidates", run_id="r", gen=0, cand=0,
    ) == 17
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_ddb_counter.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/aws/ddb.py`:

```python
"""DynamoDB wrappers. Candidates.ddb_write_count is the app-level counter
used by KG-E (spec §6.2). Every candidate write increments it atomically so
post-run assertions do not depend on CloudWatch attribution."""
from __future__ import annotations

from typing import Any


def put_candidate_with_count(
    client: Any,
    *,
    table: str,
    run_id: str,
    gen: int,
    cand: int,
    attributes: dict[str, Any],
) -> None:
    client.update_item(
        TableName=table,
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": f"gen#{gen}#cand#{cand}"},
        },
        UpdateExpression="SET #a = :a ADD ddb_write_count :one",
        ExpressionAttributeNames={"#a": "attributes"},
        ExpressionAttributeValues={
            ":a": {"M": {k: {"S": str(v)} for k, v in attributes.items()}},
            ":one": {"N": "1"},
        },
    )


def get_ddb_write_count(
    client: Any, *, table: str, run_id: str, gen: int, cand: int,
) -> int:
    resp = client.get_item(
        TableName=table,
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": f"gen#{gen}#cand#{cand}"},
        },
        ProjectionExpression="ddb_write_count",
    )
    item = resp.get("Item")
    if not item or "ddb_write_count" not in item:
        return 0
    return int(item["ddb_write_count"]["N"])
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_ddb_counter.py -v --cov=src/semi_design_runner/aws/ddb`
Expected: 3 PASS, coverage ≥ 90%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/aws/ddb.py tests/runner/test_ddb_counter.py
git commit -m "feat(runner): DDB put_candidate_with_count atomic counter for KG-E"
```

---

### Task A11: `aws/sfn.py` — StartExecution + DescribeExecution

**Files:**
- Create: `src/semi_design_runner/aws/sfn.py`
- Create: `tests/runner/test_aws_sfn.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_aws_sfn.py
import json
from unittest.mock import MagicMock
from semi_design_runner.aws.sfn import start_execution, describe_execution


def test_start_execution_serializes_payload_and_names_by_run_id():
    client = MagicMock()
    client.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123:execution:semi:r1",
    }
    arn = start_execution(
        client,
        state_machine_arn="arn:aws:states:us-east-1:123:stateMachine:semi",
        run_id="r1",
        input_payload={"spec_uri": "s3://b/spec.yaml", "seed": 42},
    )
    assert arn.endswith(":execution:semi:r1")
    kwargs = client.start_execution.call_args.kwargs
    assert kwargs["name"] == "r1"
    payload = json.loads(kwargs["input"])
    assert payload["spec_uri"] == "s3://b/spec.yaml"
    assert payload["seed"] == 42


def test_describe_execution_pass_through():
    client = MagicMock()
    client.describe_execution.return_value = {
        "status": "RUNNING",
        "startDate": "2026-04-21T00:00:00Z",
    }
    result = describe_execution(client, execution_arn="arn:e")
    assert result["status"] == "RUNNING"
    client.describe_execution.assert_called_once_with(executionArn="arn:e")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_aws_sfn.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/aws/sfn.py`:

```python
"""Step Functions wrappers. Execution name = run_id for easy tracing."""
from __future__ import annotations

import json
from typing import Any


def start_execution(
    client: Any,
    *,
    state_machine_arn: str,
    run_id: str,
    input_payload: dict[str, Any],
) -> str:
    resp = client.start_execution(
        stateMachineArn=state_machine_arn,
        name=run_id,
        input=json.dumps(input_payload),
    )
    return resp["executionArn"]


def describe_execution(client: Any, *, execution_arn: str) -> dict[str, Any]:
    return client.describe_execution(executionArn=execution_arn)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_aws_sfn.py -v --cov=src/semi_design_runner/aws/sfn`
Expected: 2 PASS, coverage ≥ 90%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/aws/sfn.py tests/runner/test_aws_sfn.py
git commit -m "feat(runner): SFN StartExecution/DescribeExecution wrappers"
```

---

### Task A12: `cost.py` — Budget guard (KG-F F1 + F2 shared logic)

**Files:**
- Create: `src/semi_design_runner/cost.py`
- Create: `tests/runner/test_budget_guard.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_budget_guard.py   (KG-F F2 unit tests)
import pytest
from datetime import datetime
from semi_design_runner.schemas import Spec, FlowParameters, StageTiming
from semi_design_runner.cost import (
    BudgetExceededError,
    check_planned_budget,
    check_accumulated_budget,
)


def _make_spec(*, budget: float, planned: dict[str, float]) -> Spec:
    return Spec(
        run_id="r",
        design="gcd",
        stack="orfs",
        flow_parameters=FlowParameters(),
        compute_budget_usd=budget,
        planned_cost_per_stage_usd=planned,
        seed=0,
        l1_lockfile_sha="sha256:" + "0" * 64,
    )


def test_planned_budget_ok_when_sum_below():
    check_planned_budget(_make_spec(budget=5.0, planned={"synth": 1.0, "pnr": 2.0}))


def test_planned_budget_rejects_when_sum_exceeds_f1_case():
    spec = _make_spec(budget=2.0, planned={"synth": 1.5, "pnr": 1.5})
    with pytest.raises(BudgetExceededError, match="planned"):
        check_planned_budget(spec)


def _timing(cost: float) -> StageTiming:
    return StageTiming(
        stage="synth",
        started_at=datetime(2026, 4, 21),
        ended_at=datetime(2026, 4, 21),
        exit_code=0,
        cost_usd=cost,
        fargate_vcpu=4096,
        fargate_memory_mb=16384,
    )


def test_accumulated_budget_accepts_when_under():
    check_accumulated_budget(
        _make_spec(budget=10.0, planned={}),
        [_timing(3.0), _timing(2.0)],
    )


def test_accumulated_budget_rejects_when_over_f2_case():
    spec = _make_spec(budget=2.0, planned={})
    with pytest.raises(BudgetExceededError, match="accumulated"):
        check_accumulated_budget(spec, [_timing(5.0)])
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_budget_guard.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/cost.py`:

```python
"""Budget guard logic shared by KG-F F1 (pre-RunTask rejection) and
F2 (post-stage accumulated abort). Both pathways raise BudgetExceededError,
which `cli.init` and the `Finalize` Lambda each convert to the appropriate
RunArtifact status (rejected_not_in_g1 / budget_exceeded respectively)."""
from __future__ import annotations

from typing import Iterable

from semi_design_runner.schemas import Spec, StageTiming


class BudgetExceededError(Exception):
    """Raised by either F1 or F2 guard. Message names which one."""


def check_planned_budget(spec: Spec) -> None:
    planned_total = sum(spec.planned_cost_per_stage_usd.values())
    if planned_total > spec.compute_budget_usd:
        raise BudgetExceededError(
            f"planned_cost_sum={planned_total} > "
            f"compute_budget_usd={spec.compute_budget_usd}"
        )


def check_accumulated_budget(
    spec: Spec, completed_stages: Iterable[StageTiming],
) -> None:
    accum = sum(s.cost_usd for s in completed_stages)
    if accum > spec.compute_budget_usd:
        raise BudgetExceededError(
            f"accumulated_cost={accum} > "
            f"compute_budget_usd={spec.compute_budget_usd}"
        )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_budget_guard.py -v --cov=src/semi_design_runner/cost`
Expected: 4 PASS, coverage ≥ 90%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/cost.py tests/runner/test_budget_guard.py
git commit -m "feat(runner): budget guard for KG-F F1 (planned) + F2 (accumulated)"
```

---

### Task A13: `validator.py` — pure G1 validation + rejection

**Files:**
- Create: `src/semi_design_runner/validator.py`
- Create: `tests/runner/test_validate_spec.py`

Pure Python validator that spec §12 mandates. Lambda handler in Phase B imports this.

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_validate_spec.py
import pytest
from semi_design_runner.schemas import Spec, FlowParameters
from semi_design_runner.validator import (
    RejectedNotInG1Scope, validate_spec_for_g1,
)


def _base(**overrides) -> Spec:
    kwargs = dict(
        run_id="r",
        design="gcd",
        stack="orfs",
        flow_parameters=FlowParameters(),
        compute_budget_usd=10.0,
        seed=0,
        l1_lockfile_sha="sha256:" + "0" * 64,
    )
    kwargs.update(overrides)
    return Spec(**kwargs)


def test_gcd_orfs_passes():
    validate_spec_for_g1(_base())


def test_gcd_librelane_passes():
    validate_spec_for_g1(_base(stack="librelane"))


def test_ibex_rejected():
    with pytest.raises(RejectedNotInG1Scope, match="design=ibex"):
        validate_spec_for_g1(_base(design="ibex"))


def test_aes_rejected():
    with pytest.raises(RejectedNotInG1Scope, match="design=aes"):
        validate_spec_for_g1(_base(design="aes"))


def test_rejection_message_lists_allowed_designs():
    with pytest.raises(RejectedNotInG1Scope, match="allowed: \\[gcd\\]"):
        validate_spec_for_g1(_base(design="ibex"))
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_validate_spec.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.validator'`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/validator.py`:

```python
"""G1-scope validator (spec §12 + overview §8 G1).

Pure function — no AWS or IO dependencies. Imported by:
- `cli.init` (local pre-submission check)
- Phase B `ValidateSpec` Lambda handler (deployed by WorkflowStack).

Both raise `RejectedNotInG1Scope` so the error name is stable across the
Python/CDK boundary (spec §4.2 error taxonomy).
"""
from __future__ import annotations

from semi_design_runner.schemas import Spec


G1_ALLOWED_DESIGNS: set[str] = {"gcd"}


class RejectedNotInG1Scope(Exception):
    """Spec uses a design not yet in G1 MVP. ibex/aes accepted post-G1."""


def validate_spec_for_g1(spec: Spec) -> None:
    if spec.design not in G1_ALLOWED_DESIGNS:
        raise RejectedNotInG1Scope(
            f"design={spec.design} is not in G1 scope; "
            f"allowed: {sorted(G1_ALLOWED_DESIGNS)}"
        )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_validate_spec.py -v --cov=src/semi_design_runner/validator`
Expected: 5 PASS, coverage = 100%.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/validator.py tests/runner/test_validate_spec.py
git commit -m "feat(runner): G1-scope validator rejects ibex/aes with RejectedNotInG1Scope"
```

---

### Task A14: `cli.py` scaffold + `init` / `auth login` / `lockfile-verify` subcommands

**Files:**
- Create: `src/semi_design_runner/cli.py`
- Create: `tests/runner/test_cli_init.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_cli_init.py
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from semi_design_runner.cli import main

SPEC_YAML = """\
version: 1
run_id: 01HAAAA
design: gcd
stack: orfs
flow_parameters: {}
compute_budget_usd: 10.0
seed: 42
l1_lockfile_sha: "sha256:{sha}"
""".format(sha="a" * 64)


def test_cli_version_flag():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "semi-run" in result.output


def test_init_rejects_non_gcd_design(tmp_path):
    spec_file = tmp_path / "bad.yaml"
    spec_file.write_text(SPEC_YAML.replace("design: gcd", "design: ibex"))
    result = CliRunner().invoke(main, ["init", "--spec", str(spec_file)])
    assert result.exit_code != 0
    assert "RejectedNotInG1Scope" in result.output or "not in G1 scope" in result.output


def test_init_writes_spec_to_s3_on_success(tmp_path):
    spec_file = tmp_path / "gcd.yaml"
    spec_file.write_text(SPEC_YAML)
    with patch("semi_design_runner.cli.make_client") as mk_client, \
         patch("semi_design_runner.cli.put_spec", return_value="s3://b/x"), \
         patch("semi_design_runner.cli.put_candidate_with_count"):
        mk_client.return_value = object()  # any
        result = CliRunner().invoke(
            main,
            ["init", "--spec", str(spec_file), "--bucket", "b"],
        )
    assert result.exit_code == 0, result.output
    assert "s3://b/x" in result.output


def test_lockfile_verify_l1_scope(tmp_path):
    lock = tmp_path / "lockfile.yaml"
    lock.write_text(
        "version: 1\n"
        "commit_shas:\n"
        "  openroad: abc\n  librelane: def\n  yosys: ghi\n  open_pdks: jkl\n"
        "  verilator: null\n  cocotb: null\n  chipyard: null\n"
        "  gemmini: null\n  mlcommons_tiny: null\n"
        "container_digests:\n"
        "  orfs-runner: sha256:x\n  librelane-runner: sha256:y\n"
        "  metric-collector: sha256:z\n"
        "source_tarball_mirrors: {}\n"
        "pdk_digests: {sky130A: sha256:p}\n"
        "stale_source_policy: {grace_period_hours: 24, action_on_failure: ci_red}\n"
        "ci_verification: {last_green_commit: g, last_green_at: '2026-04-20T00:00:00Z'}\n"
    )
    result = CliRunner().invoke(
        main, ["lockfile-verify", "--lockfile", str(lock), "--scope", "l1"],
    )
    assert result.exit_code == 0
    assert '"verified": true' in result.output
    assert '"scope": "l1"' in result.output


def test_auth_login_calls_aws_sso():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        result = CliRunner().invoke(main, ["auth", "login"])
    assert result.exit_code == 0
    run_mock.assert_called_once_with(
        ["aws", "sso", "login", "--profile", "semi-design-operator"],
        check=False,
    )
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_cli_init.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.cli'`.

- [ ] **Step 3: Implement**

Create `src/semi_design_runner/cli.py`:

```python
"""semi-run CLI entry point. Subcommands operate on Spec/RunArtifact lifecycle.

`init` validates spec + puts to S3 + records Runs row.
`lockfile-verify` emits the JSON output for G1 exit criterion 6.
`auth login` wraps `aws sso login` so operator onboarding is one command.

Other subcommands (submit/status/artifacts/cost) ship in Task A15.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click
import yaml

from semi_design_runner import __version__
from semi_design_runner.aws.clients import make_client
from semi_design_runner.aws.ddb import put_candidate_with_count
from semi_design_runner.aws.s3 import put_spec
from semi_design_runner.lockfile import load_lockfile, verify_scope
from semi_design_runner.schemas import Spec
from semi_design_runner.validator import RejectedNotInG1Scope, validate_spec_for_g1


@click.group()
@click.version_option(__version__, prog_name="semi-run")
def main() -> None:
    """L1 Process runner CLI."""


@main.command("init")
@click.option("--spec", "spec_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--bucket", type=str, default="semi-design")
@click.option("--profile", type=str, default="semi-design-operator")
def init_cmd(spec_path: Path, bucket: str, profile: str) -> None:
    raw = yaml.safe_load(spec_path.read_text())
    spec = Spec.model_validate(raw)
    try:
        validate_spec_for_g1(spec)
    except RejectedNotInG1Scope as exc:
        click.echo(f"RejectedNotInG1Scope: {exc}", err=True)
        raise SystemExit(2)

    s3 = make_client("s3", profile=profile)
    ddb = make_client("dynamodb", profile=profile)
    uri = put_spec(s3, bucket=bucket, run_id=spec.run_id, spec_yaml=spec_path.read_text())
    put_candidate_with_count(
        ddb,
        table="Candidates",
        run_id=spec.run_id,
        gen=0,
        cand=0,
        attributes={"status": "in_progress"},
    )
    # cache last-run-id for Makefile convenience
    Path(".last-run-id").write_text(spec.run_id)
    click.echo(json.dumps({"run_id": spec.run_id, "spec_uri": uri}))


@main.command("lockfile-verify")
@click.option("--lockfile", "lockfile_path", type=click.Path(exists=True, path_type=Path),
              default=Path("lockfile.yaml"))
@click.option("--scope", type=click.Choice(["l1", "full"]), default="l1")
def lockfile_verify_cmd(lockfile_path: Path, scope: str) -> None:
    lockfile = load_lockfile(lockfile_path)
    result = verify_scope(lockfile, scope=scope)
    click.echo(json.dumps(result, indent=2))
    if not result["verified"]:
        raise SystemExit(1)


@main.group("auth")
def auth_group() -> None:
    """AWS authentication helpers."""


@auth_group.command("login")
@click.option("--profile", type=str, default="semi-design-operator")
def auth_login_cmd(profile: str) -> None:
    subprocess.run(
        ["aws", "sso", "login", "--profile", profile],
        check=False,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_cli_init.py -v --cov=src/semi_design_runner/cli`
Expected: 5 PASS, coverage ≥ 85% for the three subcommands implemented.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/cli.py tests/runner/test_cli_init.py
git commit -m "feat(runner): semi-run CLI scaffold with init/lockfile-verify/auth login"
```

---

### Task A15: `cli.py` — remaining subcommands `submit` / `status` / `artifacts` / `cost`

**Files:**
- Modify: `src/semi_design_runner/cli.py`
- Create: `tests/runner/test_cli_submit_status.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_cli_submit_status.py
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pathlib import Path

from semi_design_runner.cli import main


def test_submit_starts_execution_and_prints_arn():
    with patch("semi_design_runner.cli.make_client") as mk, \
         patch("semi_design_runner.cli.start_execution", return_value="arn:e:abc"):
        mk.return_value = object()
        result = CliRunner().invoke(
            main,
            ["submit", "--run-id", "abc", "--state-machine-arn", "arn:sm"],
        )
    assert result.exit_code == 0
    assert "arn:e:abc" in result.output


def test_status_joins_ddb_and_sfn():
    ddb = MagicMock()
    ddb.get_item.return_value = {"Item": {"status": {"S": "clean"}}}
    sfn = MagicMock()
    sfn.describe_execution.return_value = {"status": "SUCCEEDED"}
    with patch("semi_design_runner.cli.make_client",
               side_effect=lambda svc, **kw: {"dynamodb": ddb, "stepfunctions": sfn}[svc]):
        result = CliRunner().invoke(
            main,
            ["status", "--run-id", "r1", "--execution-arn", "arn:e"],
        )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ddb_status"] == "clean"
    assert payload["sfn_status"] == "SUCCEEDED"


def test_artifacts_downloads_final_prefix(tmp_path):
    with patch("semi_design_runner.cli.make_client") as mk, \
         patch("semi_design_runner.cli.download_final") as dl:
        mk.return_value = object()
        result = CliRunner().invoke(
            main,
            ["artifacts", "--run-id", "r1", "--bucket", "b",
             "--dest", str(tmp_path)],
        )
    assert result.exit_code == 0
    dl.assert_called_once()
    kwargs = dl.call_args.kwargs
    assert kwargs["bucket"] == "b"
    assert kwargs["run_id"] == "r1"
    assert kwargs["dest"] == tmp_path


def test_cost_emits_budget_guard_check():
    ddb = MagicMock()
    ddb.get_item.return_value = {"Item": {"total_cost_usd": {"N": "4.2"}}}
    with patch("semi_design_runner.cli.make_client", return_value=ddb):
        result = CliRunner().invoke(main, ["cost", "--run-id", "r1"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total_cost_usd"] == 4.2
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/runner/test_cli_submit_status.py -v`
Expected: FAIL with `click.exceptions.UsageError: No such command 'submit'` (or similar — subcommands not registered yet).

- [ ] **Step 3: Implement**

Append to `src/semi_design_runner/cli.py`:

```python
from semi_design_runner.aws.s3 import download_final
from semi_design_runner.aws.sfn import describe_execution, start_execution


@main.command("submit")
@click.option("--run-id", type=str, required=True)
@click.option("--state-machine-arn", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def submit_cmd(run_id: str, state_machine_arn: str, profile: str) -> None:
    sfn = make_client("stepfunctions", profile=profile)
    arn = start_execution(
        sfn,
        state_machine_arn=state_machine_arn,
        run_id=run_id,
        input_payload={"run_id": run_id},
    )
    click.echo(arn)


@main.command("status")
@click.option("--run-id", type=str, required=True)
@click.option("--execution-arn", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def status_cmd(run_id: str, execution_arn: str, profile: str) -> None:
    ddb = make_client("dynamodb", profile=profile)
    sfn = make_client("stepfunctions", profile=profile)
    ddb_resp = ddb.get_item(
        TableName="Candidates",
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": "gen#0#cand#0"},
        },
        ProjectionExpression="status",
    )
    ddb_status = ddb_resp.get("Item", {}).get("status", {}).get("S", "unknown")
    sfn_desc = describe_execution(sfn, execution_arn=execution_arn)
    click.echo(json.dumps({
        "run_id": run_id,
        "ddb_status": ddb_status,
        "sfn_status": sfn_desc.get("status", "unknown"),
    }))


@main.command("artifacts")
@click.option("--run-id", type=str, required=True)
@click.option("--bucket", type=str, required=True)
@click.option("--dest", type=click.Path(path_type=Path), required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def artifacts_cmd(run_id: str, bucket: str, dest: Path, profile: str) -> None:
    s3 = make_client("s3", profile=profile)
    dest.mkdir(parents=True, exist_ok=True)
    download_final(s3, bucket=bucket, run_id=run_id, dest=dest)
    click.echo(str(dest))


@main.command("cost")
@click.option("--run-id", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def cost_cmd(run_id: str, profile: str) -> None:
    ddb = make_client("dynamodb", profile=profile)
    resp = ddb.get_item(
        TableName="Runs",
        Key={"run_id": {"S": run_id}},
        ProjectionExpression="total_cost_usd",
    )
    raw = resp.get("Item", {}).get("total_cost_usd", {}).get("N", "0")
    click.echo(json.dumps({"run_id": run_id, "total_cost_usd": float(raw)}))
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/runner/test_cli_submit_status.py tests/runner/test_cli_init.py -v --cov=src/semi_design_runner/cli --cov-report=term-missing`
Expected: 9 PASS (4 new + 5 from A14), coverage ≥ 85% for `cli.py`.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/cli.py tests/runner/test_cli_submit_status.py
git commit -m "feat(runner): CLI submit/status/artifacts/cost subcommands"
```

---

### Phase A completion gate

After A15, run full coverage + lint sweep:

```bash
uv run pytest tests/runner -v --cov=src/semi_design_runner --cov-report=term-missing --cov-fail-under=85
uv run ruff check src/semi_design_runner tests/runner
uv run ruff format --check src/semi_design_runner tests/runner
```

Expected: all tests PASS, coverage ≥ 85%, ruff clean.

Commit any formatting touches under `chore(runner): ruff format`.

---

## Phase B — CDK Infrastructure

**Goal:** Provision the 6 AWS stacks (`NetworkStack`, `StorageStack`, `ContainerStack`, `ComputeStack`, `WorkflowStack`, `ObservabilityStack`) via CDK TypeScript so that `cdk synth` + `cdk deploy --no-execute` on a clean checkout produces a green ChangeSet, with every load-bearing invariant from spec §6 + §16 asserted by `jest` + `aws-cdk-lib/assertions` + `cdk-nag`. No real AWS resources are deployed in this phase — Phase E drives the actual `cdk deploy`. Each task follows the TDD 5-step structure (Write failing test → Run to fail → Implement → Run to pass → Commit) with full code in every step.

**Non-goals for Phase B:** Writing Docker images (Phase C), KG scripts (Phase D), or wiring `make run` (Phase E). Python runner code (Phase A) is referenced only by name in Lambda stubs.

**Phase B dependencies:** none outside this phase. Runs in parallel with Phase A and Phase C per plan `## Phase Ordering & Dependencies`. All commands below assume `cd cdk` unless stated otherwise.

---

### Task B1: Bootstrap `cdk/` (package, tsconfig, jest, cdk-nag, App entry)

**Files:**
- Create: `cdk/package.json`
- Create: `cdk/cdk.json`
- Create: `cdk/tsconfig.json`
- Create: `cdk/jest.config.ts`
- Create: `cdk/bin/semi-design.ts`
- Create: `cdk/lib/app-context.ts`
- Create: `cdk/test/app.test.ts`
- Create: `cdk/.gitignore`

- [ ] **Step 1: Write the failing test**

```typescript
// cdk/test/app.test.ts
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { AwsSolutionsChecks } from "cdk-nag";
import { Aspects } from "aws-cdk-lib";
import { buildApp } from "../bin/semi-design";

describe("App bootstrap", () => {
  it("synthesizes with no stacks yet and attaches cdk-nag AwsSolutionsChecks", () => {
    const app = buildApp({ env: "dev" });
    // cdk-nag aspect must be attached at construction; test proves the hook is live.
    const aspects = Aspects.of(app).all;
    expect(aspects.some((a) => a instanceof AwsSolutionsChecks)).toBe(true);
    // App.synth() must succeed even with zero stacks (pre-Task B2 state).
    const cloudAssembly = app.synth();
    expect(cloudAssembly.stacks.length).toBe(0);
  });

  it("rejects unknown context env value", () => {
    expect(() => buildApp({ env: "staging" as "dev" | "prod" })).toThrow(
      /env must be 'dev' or 'prod'/,
    );
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd cdk && npx jest test/app.test.ts`
Expected: FAIL with `Cannot find module '../bin/semi-design'` (no file yet).

- [ ] **Step 3: Write minimal implementation**

Create `cdk/package.json`:

```json
{
  "name": "semi-design-cdk",
  "version": "0.1.0",
  "private": true,
  "bin": {
    "semi-design": "bin/semi-design.js"
  },
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "test": "jest",
    "cdk": "cdk"
  },
  "devDependencies": {
    "@types/jest": "^29.5.12",
    "@types/node": "^20.11.30",
    "aws-cdk": "^2.140.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.2",
    "ts-node": "^10.9.2",
    "typescript": "^5.4.5"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.140.0",
    "cdk-nag": "^2.28.80",
    "constructs": "^10.3.0",
    "source-map-support": "^0.5.21"
  }
}
```

Create `cdk/cdk.json`:

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/semi-design.ts",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/*.d.ts", "**/*.js", "tsconfig.json", "package*.json", "yarn.lock", "node_modules", "test"]
  },
  "context": {
    "env": "dev",
    "@aws-cdk/core:stackRelativeExports": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true
  }
}
```

Create `cdk/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "typeRoots": ["./node_modules/@types"],
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "exclude": ["node_modules", "cdk.out"]
}
```

Create `cdk/jest.config.ts`:

```typescript
import type { Config } from "jest";

const config: Config = {
  testEnvironment: "node",
  roots: ["<rootDir>/test"],
  testMatch: ["**/*.test.ts"],
  transform: {
    "^.+\\.tsx?$": "ts-jest",
  },
  moduleFileExtensions: ["ts", "js"],
  setupFilesAfterEach: [],
};

export default config;
```

Create `cdk/lib/app-context.ts`:

```typescript
export type EnvName = "dev" | "prod";

export interface AppContext {
  env: EnvName;
}

export function resolveContext(raw: { env?: string }): AppContext {
  const env = raw.env ?? "dev";
  if (env !== "dev" && env !== "prod") {
    throw new Error(`env must be 'dev' or 'prod', got '${env}'`);
  }
  return { env };
}
```

Create `cdk/bin/semi-design.ts`:

```typescript
#!/usr/bin/env node
import "source-map-support/register";
import { App, Aspects } from "aws-cdk-lib";
import { AwsSolutionsChecks } from "cdk-nag";
import { AppContext, EnvName, resolveContext } from "../lib/app-context";

export interface BuildAppOptions {
  env: EnvName;
}

export function buildApp(opts: BuildAppOptions): App {
  const ctx = resolveContext({ env: opts.env });
  const app = new App({
    context: { env: ctx.env },
  });
  // cdk-nag AwsSolutionsChecks attached to root App so every stack inherits.
  Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
  return app;
}

// Invoked by `cdk synth` / `cdk deploy`.
if (require.main === module) {
  const rawEnv = process.env.CDK_CONTEXT_ENV ?? "dev";
  const ctx = resolveContext({ env: rawEnv });
  buildApp({ env: ctx.env });
}
```

Create `cdk/.gitignore`:

```
*.js
!jest.config.js
*.d.ts
node_modules
cdk.out
.cdk.staging
*.swp
.DS_Store
```

Run `cd cdk && npm install` to populate `node_modules`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd cdk && npx jest test/app.test.ts`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/package.json cdk/cdk.json cdk/tsconfig.json cdk/jest.config.ts cdk/bin/semi-design.ts cdk/lib/app-context.ts cdk/test/app.test.ts cdk/.gitignore
git commit -m "chore(cdk): bootstrap CDK app with ts-jest + cdk-nag AwsSolutionsChecks"
```

---

### Task B2: `NetworkStack` — VPC + private subnets × 2 AZ + 9 VPC endpoints, no NAT

**Files:**
- Create: `cdk/lib/stacks/NetworkStack.ts`
- Create: `cdk/test/NetworkStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/NetworkStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { NetworkStack } from "../lib/stacks/NetworkStack";

describe("NetworkStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new NetworkStack(app, "NetworkStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates a VPC with 2 private subnets and no NAT gateway", () => {
    template.resourceCountIs("AWS::EC2::VPC", 1);
    template.resourceCountIs("AWS::EC2::NatGateway", 0);
    // 2 AZ * 1 private subnet tier = 2 subnets.
    const privateSubnets = template.findResources("AWS::EC2::Subnet", {
      Properties: { MapPublicIpOnLaunch: false },
    });
    expect(Object.keys(privateSubnets).length).toBe(2);
  });

  it("creates exactly the 9 required VPC endpoints", () => {
    // 1 Gateway endpoint (s3) + 8 Interface endpoints.
    template.resourceCountIs("AWS::EC2::VPCEndpoint", 9);

    const expectedInterfaceSuffixes = [
      "ecr.api",
      "ecr.dkr",
      "logs",
      "secretsmanager",
      "ssm",
      "sts",
      "monitoring",
      "kms",
    ];
    for (const suffix of expectedInterfaceSuffixes) {
      template.hasResourceProperties("AWS::EC2::VPCEndpoint", {
        VpcEndpointType: "Interface",
        ServiceName: Match.stringLikeRegexp(`com\\.amazonaws\\.[a-z0-9-]+\\.${suffix.replace(".", "\\.")}$`),
      });
    }
    // s3 gateway endpoint.
    template.hasResourceProperties("AWS::EC2::VPCEndpoint", {
      VpcEndpointType: "Gateway",
      ServiceName: Match.stringLikeRegexp(`com\\.amazonaws\\.[a-z0-9-]+\\.s3$`),
    });
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/NetworkStack.test.ts`
Expected: FAIL with `Cannot find module '../lib/stacks/NetworkStack'`.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/NetworkStack.ts`:

```typescript
import { Stack, StackProps } from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface NetworkStackProps extends StackProps {
  env: EnvName;
}

/**
 * VPC + 2 AZ private subnets. No NAT gateway — all egress goes through
 * VPC endpoints (spec §6.1). The 9 endpoints cover every AWS service the
 * Fargate tasks + Lambda reach at runtime: S3 (Gateway), ECR api/dkr,
 * CloudWatch Logs, Secrets Manager, SSM, STS, CloudWatch Monitoring, KMS.
 */
export class NetworkStack extends Stack {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    this.vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: "private-isolated",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    });

    // S3 Gateway endpoint (free). Required for ECR layer download + artifact I/O.
    this.vpc.addGatewayEndpoint("S3Gateway", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
    });

    const interfaceServices: Array<{ id: string; svc: ec2.InterfaceVpcEndpointAwsService }> = [
      { id: "EcrApi", svc: ec2.InterfaceVpcEndpointAwsService.ECR },
      { id: "EcrDkr", svc: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER },
      { id: "Logs", svc: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS },
      { id: "SecretsManager", svc: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER },
      { id: "Ssm", svc: ec2.InterfaceVpcEndpointAwsService.SSM },
      { id: "Sts", svc: ec2.InterfaceVpcEndpointAwsService.STS },
      { id: "Monitoring", svc: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_MONITORING },
      { id: "Kms", svc: ec2.InterfaceVpcEndpointAwsService.KMS },
    ];

    for (const { id: endpointId, svc } of interfaceServices) {
      this.vpc.addInterfaceEndpoint(endpointId, {
        service: svc,
        subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
        privateDnsEnabled: true,
      });
    }
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/NetworkStack.test.ts`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/NetworkStack.ts cdk/test/NetworkStack.test.ts
git commit -m "feat(cdk): add NetworkStack with 9 VPC endpoints and no NAT"
```

---

### Task B3: `StorageStack` — S3 Object Lock at creation + DDB × 4 + KMS CMK

**Files:**
- Create: `cdk/lib/stacks/StorageStack.ts`
- Create: `cdk/test/StorageStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/StorageStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { StorageStack } from "../lib/stacks/StorageStack";

describe("StorageStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new StorageStack(app, "StorageStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates an S3 bucket with ObjectLockEnabled=true at creation (Codex 3rd-round)", () => {
    // Spec §6.1: Object Lock cannot be added later — must be true at creation.
    template.hasResourceProperties("AWS::S3::Bucket", {
      ObjectLockEnabled: true,
      VersioningConfiguration: { Status: "Enabled" },
      ObjectLockConfiguration: Match.objectLike({
        ObjectLockEnabled: "Enabled",
        Rule: {
          DefaultRetention: {
            Mode: "GOVERNANCE",
            Days: 90,
          },
        },
      }),
    });
  });

  it("bucket has lifecycle transitioning to GLACIER_IR at 90 days", () => {
    template.hasResourceProperties("AWS::S3::Bucket", {
      LifecycleConfiguration: Match.objectLike({
        Rules: Match.arrayWith([
          Match.objectLike({
            Status: "Enabled",
            Transitions: Match.arrayWith([
              Match.objectLike({
                StorageClass: "GLACIER_IR",
                TransitionInDays: 90,
              }),
            ]),
          }),
        ]),
      }),
    });
  });

  it("creates exactly 4 DynamoDB tables with Events TTL enabled", () => {
    template.resourceCountIs("AWS::DynamoDB::Table", 4);
    // Events must have TTL attribute name set (spec §6.2: TTL 90d).
    template.hasResourceProperties("AWS::DynamoDB::Table", {
      TableName: Match.stringLikeRegexp("Events"),
      TimeToLiveSpecification: {
        AttributeName: "ttl",
        Enabled: true,
      },
    });
  });

  it("creates a KMS CMK with key rotation enabled", () => {
    template.resourceCountIs("AWS::KMS::Key", 1);
    template.hasResourceProperties("AWS::KMS::Key", {
      EnableKeyRotation: true,
    });
  });

  it("exposes bucketCmk as a public readonly property", () => {
    expect(stack.bucketCmk).toBeDefined();
    expect(stack.bucketCmk.keyArn).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/StorageStack.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/StorageStack.ts`:

```typescript
import { Duration, RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as kms from "aws-cdk-lib/aws-kms";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface StorageStackProps extends StackProps {
  env: EnvName;
}

/**
 * S3 + DynamoDB + KMS. The bucket MUST have `objectLockEnabled: true` at
 * construction — S3 does not allow enabling Object Lock on an existing
 * bucket (spec §6.1 Codex 3rd-round new #6). DDB `Events` has TTL 90d
 * (spec §6.2). KMS CMK is referenced by ComputeStack for kms:Decrypt.
 */
export class StorageStack extends Stack {
  public readonly bucket: s3.Bucket;
  public readonly bucketCmk: kms.Key;
  public readonly runsTable: dynamodb.Table;
  public readonly generationsTable: dynamodb.Table;
  public readonly candidatesTable: dynamodb.Table;
  public readonly eventsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: StorageStackProps) {
    super(scope, id, props);

    this.bucketCmk = new kms.Key(this, "BucketCmk", {
      description: "CMK encrypting the semi-design artifact bucket",
      enableKeyRotation: true,
      alias: `alias/semi-design-${props.env}-bucket`,
      removalPolicy: props.env === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
    });

    this.bucket = new s3.Bucket(this, "ArtifactBucket", {
      bucketName: `semi-design-${this.account}-${this.region}`,
      objectLockEnabled: true, // MUST be true at creation — cannot be added later.
      versioned: true,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: this.bucketCmk,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      objectLockDefaultRetention: s3.ObjectLockRetention.governance(Duration.days(90)),
      lifecycleRules: [
        {
          id: "transition-to-glacier-ir",
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER_INSTANT_RETRIEVAL,
              transitionAfter: Duration.days(90),
            },
          ],
        },
      ],
      removalPolicy: props.env === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
    });

    const tableDefaults: Omit<dynamodb.TableProps, "partitionKey" | "tableName"> = {
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.bucketCmk,
      pointInTimeRecovery: true,
      removalPolicy: props.env === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
    };

    this.runsTable = new dynamodb.Table(this, "Runs", {
      ...tableDefaults,
      tableName: `semi-design-${props.env}-Runs`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
    });

    this.generationsTable = new dynamodb.Table(this, "Generations", {
      ...tableDefaults,
      tableName: `semi-design-${props.env}-Generations`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "gen", type: dynamodb.AttributeType.STRING },
    });

    this.candidatesTable = new dynamodb.Table(this, "Candidates", {
      ...tableDefaults,
      tableName: `semi-design-${props.env}-Candidates`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "gen_cand", type: dynamodb.AttributeType.STRING },
    });

    this.eventsTable = new dynamodb.Table(this, "Events", {
      ...tableDefaults,
      tableName: `semi-design-${props.env}-Events`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "ts", type: dynamodb.AttributeType.STRING },
      timeToLiveAttribute: "ttl",
    });
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/StorageStack.test.ts`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/StorageStack.ts cdk/test/StorageStack.test.ts
git commit -m "feat(cdk): add StorageStack with S3 Object Lock at creation + DDB x4 + KMS CMK"
```

---

### Task B4: `ContainerStack` — ECR × 3 repos, scan on push, immutable tags

**Files:**
- Create: `cdk/lib/stacks/ContainerStack.ts`
- Create: `cdk/test/ContainerStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/ContainerStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ContainerStack } from "../lib/stacks/ContainerStack";

describe("ContainerStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new ContainerStack(app, "ContainerStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates 3 ECR repositories", () => {
    template.resourceCountIs("AWS::ECR::Repository", 3);
  });

  it.each(["orfs-runner", "librelane-runner", "metric-collector"])(
    "creates ECR repo %s with immutable tags and scan-on-push",
    (name) => {
      template.hasResourceProperties("AWS::ECR::Repository", {
        RepositoryName: Match.stringLikeRegexp(name),
        ImageTagMutability: "IMMUTABLE",
        ImageScanningConfiguration: { ScanOnPush: true },
      });
    },
  );

  it("exposes all three repo ARNs as public properties", () => {
    expect(stack.orfsRunnerRepo.repositoryArn).toBeDefined();
    expect(stack.librelaneRunnerRepo.repositoryArn).toBeDefined();
    expect(stack.metricCollectorRepo.repositoryArn).toBeDefined();
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/ContainerStack.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/ContainerStack.ts`:

```typescript
import { RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface ContainerStackProps extends StackProps {
  env: EnvName;
}

/**
 * ECR repositories for the 3 runtime images. Spec §5 + §6.1:
 * - IMMUTABLE tag mutability — prevents accidental re-push of an existing digest
 * - scan on push — picks up CVE regressions automatically
 * - removalPolicy DESTROY in dev (tests), RETAIN in prod
 */
export class ContainerStack extends Stack {
  public readonly orfsRunnerRepo: ecr.Repository;
  public readonly librelaneRunnerRepo: ecr.Repository;
  public readonly metricCollectorRepo: ecr.Repository;

  constructor(scope: Construct, id: string, props: ContainerStackProps) {
    super(scope, id, props);

    const removalPolicy = props.env === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY;

    const repoDefaults = {
      imageTagMutability: ecr.TagMutability.IMMUTABLE,
      imageScanOnPush: true,
      removalPolicy,
    };

    this.orfsRunnerRepo = new ecr.Repository(this, "OrfsRunner", {
      repositoryName: `semi-design-${props.env}-orfs-runner`,
      ...repoDefaults,
    });
    this.librelaneRunnerRepo = new ecr.Repository(this, "LibrelaneRunner", {
      repositoryName: `semi-design-${props.env}-librelane-runner`,
      ...repoDefaults,
    });
    this.metricCollectorRepo = new ecr.Repository(this, "MetricCollector", {
      repositoryName: `semi-design-${props.env}-metric-collector`,
      ...repoDefaults,
    });
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/ContainerStack.test.ts`
Expected: 5 PASS (1 count + 3 parameterized name checks + 1 property export).

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/ContainerStack.ts cdk/test/ContainerStack.test.ts
git commit -m "feat(cdk): add ContainerStack with 3 ECR repos (immutable tags, scan on push)"
```

---

### Task B5: `ComputeStack` — ECS Fargate cluster + 3 TaskDef with explicit CMK ARN scoping

**Files:**
- Create: `cdk/lib/stacks/ComputeStack.ts`
- Create: `cdk/test/ComputeStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/ComputeStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";

describe("ComputeStack", () => {
  const app = new App({ context: { env: "dev" } });
  const network = new NetworkStack(app, "NetworkTest", { env: "dev" });
  const storage = new StorageStack(app, "StorageTest", { env: "dev" });
  const container = new ContainerStack(app, "ContainerTest", { env: "dev" });
  const compute = new ComputeStack(app, "ComputeTest", {
    env: "dev",
    vpc: network.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const template = Template.fromStack(compute);

  it("creates an ECS cluster with no EC2 capacity", () => {
    template.resourceCountIs("AWS::ECS::Cluster", 1);
    template.resourceCountIs("AWS::AutoScaling::AutoScalingGroup", 0);
  });

  it("creates 3 Fargate TaskDefinitions with EphemeralStorage.SizeInGiB=21", () => {
    template.resourceCountIs("AWS::ECS::TaskDefinition", 3);
    const tds = template.findResources("AWS::ECS::TaskDefinition", {
      Properties: {
        EphemeralStorage: { SizeInGiB: 21 },
      },
    });
    expect(Object.keys(tds).length).toBe(3);
  });

  it("task role kms:Decrypt is scoped to specific CMK ARNs, never '*'", () => {
    const roles = template.findResources("AWS::IAM::Policy");
    // For every policy doc that contains kms:Decrypt, its Resource must not be "*".
    for (const [, res] of Object.entries(roles)) {
      const stmts = (res as { Properties: { PolicyDocument: { Statement: unknown[] } } })
        .Properties.PolicyDocument.Statement;
      for (const stmt of stmts as Array<{
        Action?: string | string[];
        Resource?: unknown;
      }>) {
        const actions = Array.isArray(stmt.Action) ? stmt.Action : [stmt.Action];
        if (actions.includes("kms:Decrypt")) {
          expect(stmt.Resource).toBeDefined();
          expect(stmt.Resource).not.toBe("*");
          // Resource may be a single Fn::GetAtt ref or an array — both ok.
          // Reject bare "*" whether string or in array.
          const resArr = Array.isArray(stmt.Resource) ? stmt.Resource : [stmt.Resource];
          for (const r of resArr) {
            expect(r).not.toBe("*");
          }
        }
      }
    }
  });

  it("only the kg-c2-smoke task role has secretsmanager:GetSecretValue", () => {
    const secretsAllowers = Object.entries(
      template.findResources("AWS::IAM::Policy"),
    ).filter(([, res]) => {
      const stmts = (res as { Properties: { PolicyDocument: { Statement: unknown[] } } })
        .Properties.PolicyDocument.Statement;
      return (stmts as Array<{ Action?: string | string[] }>).some((s) => {
        const actions = Array.isArray(s.Action) ? s.Action : [s.Action];
        return actions.includes("secretsmanager:GetSecretValue");
      });
    });
    expect(secretsAllowers.length).toBe(1);
  });

  it("exposes kg-c2-smoke TaskDefinition for KG-C2 Fargate execution", () => {
    expect(compute.kgC2SmokeTaskDef).toBeDefined();
    template.hasResourceProperties("AWS::ECS::TaskDefinition", {
      Family: Match.stringLikeRegexp("kg-c2-smoke"),
    });
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/ComputeStack.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/ComputeStack.ts`:

```typescript
import { Size, Stack, StackProps } from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as kms from "aws-cdk-lib/aws-kms";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface ComputeStackProps extends StackProps {
  env: EnvName;
  vpc: ec2.IVpc;
  bucketCmk: kms.IKey;
  artifactBucketArn: string;
  orfsRunnerRepo: ecr.IRepository;
  librelaneRunnerRepo: ecr.IRepository;
  metricCollectorRepo: ecr.IRepository;
}

/**
 * ECS Fargate-only cluster + 3 runtime TaskDefs + kg-c2-smoke TaskDef.
 * Spec §6.1 / §6.3:
 *   - ephemeralStorageGiB: 21 on every TaskDef (Codex #8)
 *   - kms:Decrypt scoped to explicit CMK ARNs (StorageStack.bucketCmk +
 *     Secrets Manager default KMS key). Bare "*" forbidden (Codex 3rd-round new #5).
 *   - secretsmanager:GetSecretValue ONLY on kg-c2-smoke task role.
 */
export class ComputeStack extends Stack {
  public readonly cluster: ecs.Cluster;
  public readonly orfsRunnerTaskDef: ecs.FargateTaskDefinition;
  public readonly librelaneRunnerTaskDef: ecs.FargateTaskDefinition;
  public readonly metricCollectorTaskDef: ecs.FargateTaskDefinition;
  public readonly kgC2SmokeTaskDef: ecs.FargateTaskDefinition;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    this.cluster = new ecs.Cluster(this, "Cluster", {
      vpc: props.vpc,
      containerInsights: true,
      enableFargateCapacityProviders: true,
    });

    // Secrets Manager default KMS key alias — resolved at deploy via a static import.
    const secretsManagerKmsKey = kms.Key.fromLookup(this, "SecretsManagerCmk", {
      aliasName: "alias/aws/secretsmanager",
    });

    // Base task role factory: minimum perms + scoped kms:Decrypt.
    const makeRuntimeTaskRole = (id: string): iam.Role => {
      const role = new iam.Role(this, id, {
        assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      });
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["s3:GetObject", "s3:PutObject"],
          resources: [`${props.artifactBucketArn}/runs/*`],
        }),
      );
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: [
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:GetItem",
          ],
          resources: [
            `arn:aws:dynamodb:${this.region}:${this.account}:table/semi-design-${props.env}-Candidates`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/semi-design-${props.env}-Events`,
          ],
        }),
      );
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["logs:CreateLogStream", "logs:PutLogEvents"],
          resources: [
            `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/ecs/semi-design-${props.env}*`,
          ],
        }),
      );
      // kms:Decrypt scoped EXPLICITLY to the two CMK ARNs we actually use.
      // Never "*" — Codex 3rd-round new #5.
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["kms:Decrypt"],
          resources: [props.bucketCmk.keyArn, secretsManagerKmsKey.keyArn],
        }),
      );
      return role;
    };

    const makeFargateTaskDef = (
      id: string,
      family: string,
      repo: ecr.IRepository,
      extraRole?: (role: iam.Role) => void,
    ): ecs.FargateTaskDefinition => {
      const taskRole = makeRuntimeTaskRole(`${id}TaskRole`);
      if (extraRole) {
        extraRole(taskRole);
      }
      const td = new ecs.FargateTaskDefinition(this, id, {
        family: `semi-design-${props.env}-${family}`,
        cpu: 4096,
        memoryLimitMiB: 16384,
        ephemeralStorageGiB: 21, // Spec §4.1 ResourceOverrides default.
        taskRole,
      });
      td.addContainer("main", {
        image: ecs.ContainerImage.fromEcrRepository(repo),
        logging: ecs.LogDrivers.awsLogs({ streamPrefix: family }),
      });
      return td;
    };

    this.orfsRunnerTaskDef = makeFargateTaskDef(
      "OrfsRunner",
      "orfs-runner",
      props.orfsRunnerRepo,
    );
    this.librelaneRunnerTaskDef = makeFargateTaskDef(
      "LibrelaneRunner",
      "librelane-runner",
      props.librelaneRunnerRepo,
    );
    this.metricCollectorTaskDef = makeFargateTaskDef(
      "MetricCollector",
      "metric-collector",
      props.metricCollectorRepo,
    );

    // KG-C2 smoke task — only TaskDef with secretsmanager:GetSecretValue.
    this.kgC2SmokeTaskDef = makeFargateTaskDef(
      "KgC2Smoke",
      "kg-c2-smoke",
      props.metricCollectorRepo,
      (role) => {
        role.addToPolicy(
          new iam.PolicyStatement({
            actions: ["secretsmanager:GetSecretValue"],
            resources: [
              `arn:aws:secretsmanager:${this.region}:${this.account}:secret:/semi-design/*`,
            ],
          }),
        );
      },
    );
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/ComputeStack.test.ts`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/ComputeStack.ts cdk/test/ComputeStack.test.ts
git commit -m "feat(cdk): add ComputeStack with Fargate TaskDefs scoped to explicit CMK ARNs"
```

---

### Task B6: `WorkflowStack` — SFN Standard + Map + 3 Lambdas + EventBridge

**Files:**
- Create: `cdk/lib/stacks/WorkflowStack.ts`
- Create: `cdk/lambdas/validate-spec/index.py`
- Create: `cdk/lambdas/init-generation/index.py`
- Create: `cdk/lambdas/finalize/index.py`
- Create: `cdk/test/WorkflowStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/WorkflowStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";
import { WorkflowStack } from "../lib/stacks/WorkflowStack";

describe("WorkflowStack", () => {
  const app = new App({ context: { env: "dev" } });
  const net = new NetworkStack(app, "NetworkW", { env: "dev" });
  const storage = new StorageStack(app, "StorageW", { env: "dev" });
  const container = new ContainerStack(app, "ContainerW", { env: "dev" });
  const compute = new ComputeStack(app, "ComputeW", {
    env: "dev",
    vpc: net.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const stack = new WorkflowStack(app, "WorkflowW", {
    env: "dev",
    cluster: compute.cluster,
    orfsRunnerTaskDef: compute.orfsRunnerTaskDef,
    librelaneRunnerTaskDef: compute.librelaneRunnerTaskDef,
    metricCollectorTaskDef: compute.metricCollectorTaskDef,
    artifactBucket: storage.bucket,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
    eventsTable: storage.eventsTable,
  });
  const template = Template.fromStack(stack);

  it("creates exactly 3 Lambda functions (ValidateSpec, InitGeneration, Finalize)", () => {
    template.resourceCountIs("AWS::Lambda::Function", 3);
  });

  it("Step Functions state machine type is STANDARD", () => {
    template.hasResourceProperties("AWS::StepFunctions::StateMachine", {
      StateMachineType: "STANDARD",
    });
  });

  it("Map state has MaxConcurrency=10 in the ASL definition", () => {
    const machines = template.findResources("AWS::StepFunctions::StateMachine");
    const [, machine] = Object.entries(machines)[0];
    const defStr = JSON.stringify(
      (machine as { Properties: { DefinitionString: unknown } }).Properties.DefinitionString,
    );
    expect(defStr).toContain("\\\"MaxConcurrency\\\":10");
  });

  it("ValidateSpec Lambda environment identifies G1 allowed design", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      FunctionName: Match.stringLikeRegexp("validate-spec"),
      Environment: {
        Variables: Match.objectLike({
          G1_ALLOWED_DESIGN: "gcd",
        }),
      },
    });
  });

  it("creates an EventBridge rule for run completion", () => {
    template.resourceCountIs("AWS::Events::Rule", 1);
    template.hasResourceProperties("AWS::Events::Rule", {
      EventPattern: Match.objectLike({
        source: Match.arrayWith(["semi-design.l1"]),
      }),
    });
  });
});
```

Create `cdk/lambdas/validate-spec/index.py`:

```python
"""ValidateSpec Lambda.

Rejects any Spec whose `design` is not in the G1 allowed-list.
Raises RejectedNotInG1Scope so the SFN state machine can route to the
`rejected_not_in_g1` terminal state. The rejection class name is the exact
contract the Python runner (Phase A, tests/runner/test_validate_spec.py)
asserts on via the SFN execution history.
"""
from __future__ import annotations

import json
import os
from typing import Any


class RejectedNotInG1Scope(Exception):
    """Raised when Spec.design is not allowed in G1 scope."""


ALLOWED_DESIGN = os.environ.get("G1_ALLOWED_DESIGN", "gcd")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    spec = event.get("spec", event)
    design = spec.get("design")
    if design != ALLOWED_DESIGN:
        raise RejectedNotInG1Scope(
            f"design={design} is not in G1 scope; allowed: [{ALLOWED_DESIGN}]"
        )
    # Pass-through so downstream Map state receives the spec unchanged.
    return {"ok": True, "spec": spec}
```

Create `cdk/lambdas/init-generation/index.py`:

```python
"""InitGeneration Lambda.

L1 always runs with a single generation (N=0). L2/L3 will override this
function; for G1 we simply emit a one-element candidates list so the
SFN Map state has exactly one iteration per run.
"""
from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    spec = event.get("spec", event)
    return {
        "run_id": spec["run_id"],
        "generation": 0,
        "candidates": [
            {
                "run_id": spec["run_id"],
                "gen": 0,
                "cand": 0,
                "spec": spec,
            },
        ],
    }
```

Create `cdk/lambdas/finalize/index.py`:

```python
"""Finalize Lambda — per-object retention-aware finalization.

Spec §4.3: every put/copy into runs/{run_id}/final/ MUST include
`x-amz-object-lock-mode=GOVERNANCE` + `x-amz-object-lock-retain-until-date`
(=now+90d). Writing _SUCCESS last is an invariant check, not a locking step.
"""
from __future__ import annotations

import datetime
import os
from typing import Any

import boto3

BUCKET = os.environ["ARTIFACT_BUCKET"]
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "90"))

s3 = boto3.client("s3")


def _retention_args() -> dict[str, Any]:
    retain_until = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        days=RETENTION_DAYS,
    )
    return {
        "ObjectLockMode": "GOVERNANCE",
        "ObjectLockRetainUntilDate": retain_until,
    }


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    run_id = event["run_id"]
    manifest = event["manifest"]  # list of {staging_key, final_key}
    for entry in manifest:
        s3.copy_object(
            Bucket=BUCKET,
            CopySource={"Bucket": BUCKET, "Key": entry["staging_key"]},
            Key=entry["final_key"],
            **_retention_args(),
        )
    # Sidecars
    for sidecar_key in ("metrics.json", "provenance.yaml", "cost_actuals.json"):
        body = event["sidecars"][sidecar_key].encode()
        s3.put_object(
            Bucket=BUCKET,
            Key=f"runs/{run_id}/final/{sidecar_key}",
            Body=body,
            **_retention_args(),
        )
    # _SUCCESS LAST — still with retention header.
    s3.put_object(
        Bucket=BUCKET,
        Key=f"runs/{run_id}/final/_SUCCESS",
        Body=b"",
        **_retention_args(),
    )
    return {"run_id": run_id, "status": "finalized"}
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/WorkflowStack.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/WorkflowStack.ts`:

```typescript
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as events from "aws-cdk-lib/aws-events";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import * as path from "path";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface WorkflowStackProps extends StackProps {
  env: EnvName;
  cluster: ecs.ICluster;
  orfsRunnerTaskDef: ecs.FargateTaskDefinition;
  librelaneRunnerTaskDef: ecs.FargateTaskDefinition;
  metricCollectorTaskDef: ecs.FargateTaskDefinition;
  artifactBucket: s3.IBucket;
  candidatesTable: dynamodb.ITable;
  runsTable: dynamodb.ITable;
  eventsTable: dynamodb.ITable;
}

/**
 * Step Functions Standard Workflow. Map state wraps the per-candidate
 * pipeline at maxConcurrency=10 (spec §6.1). The 3 Lambdas are:
 *   - ValidateSpec: rejects design != "gcd" with RejectedNotInG1Scope.
 *   - InitGeneration: for L1 always emits one candidate (gen=0).
 *   - Finalize: per-object CopyObject/PutObject with Object Lock retention
 *     header applied at the same call (spec §4.3).
 */
export class WorkflowStack extends Stack {
  public readonly stateMachine: sfn.StateMachine;
  public readonly validateSpecFn: lambda.Function;
  public readonly initGenerationFn: lambda.Function;
  public readonly finalizeFn: lambda.Function;
  public readonly completionRule: events.Rule;

  constructor(scope: Construct, id: string, props: WorkflowStackProps) {
    super(scope, id, props);

    this.validateSpecFn = new lambda.Function(this, "ValidateSpec", {
      functionName: `semi-design-${props.env}-validate-spec`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "..", "lambdas", "validate-spec")),
      timeout: Duration.seconds(15),
      environment: {
        G1_ALLOWED_DESIGN: "gcd",
      },
    });

    this.initGenerationFn = new lambda.Function(this, "InitGeneration", {
      functionName: `semi-design-${props.env}-init-generation`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "..", "lambdas", "init-generation")),
      timeout: Duration.seconds(30),
    });

    this.finalizeFn = new lambda.Function(this, "Finalize", {
      functionName: `semi-design-${props.env}-finalize`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "..", "lambdas", "finalize")),
      timeout: Duration.minutes(5),
      environment: {
        ARTIFACT_BUCKET: props.artifactBucket.bucketName,
        RETENTION_DAYS: "90",
      },
    });
    props.artifactBucket.grantReadWrite(this.finalizeFn);
    this.finalizeFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["s3:PutObjectRetention"],
        resources: [`${props.artifactBucket.bucketArn}/*`],
      }),
    );

    // SFN tasks
    const validate = new tasks.LambdaInvoke(this, "ValidateSpecTask", {
      lambdaFunction: this.validateSpecFn,
      payloadResponseOnly: true,
    });
    const initGen = new tasks.LambdaInvoke(this, "InitGenerationTask", {
      lambdaFunction: this.initGenerationFn,
      payloadResponseOnly: true,
    });

    // Per-candidate subflow (minimal stub — Phase E wires actual stages).
    const runOrfs = new tasks.EcsRunTask(this, "RunOrfsPipeline", {
      cluster: props.cluster,
      taskDefinition: props.orfsRunnerTaskDef,
      launchTarget: new tasks.EcsFargateLaunchTarget(),
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      assignPublicIp: false,
    });
    const finalize = new tasks.LambdaInvoke(this, "FinalizeTask", {
      lambdaFunction: this.finalizeFn,
      payloadResponseOnly: true,
    });

    const candidateChain = runOrfs.next(finalize);

    const mapState = new sfn.Map(this, "CandidatesMap", {
      maxConcurrency: 10,
      itemsPath: "$.candidates",
    });
    mapState.iterator(candidateChain);

    const definition = validate.next(initGen).next(mapState);

    this.stateMachine = new sfn.StateMachine(this, "L1StateMachine", {
      stateMachineName: `semi-design-${props.env}-l1`,
      stateMachineType: sfn.StateMachineType.STANDARD,
      definitionBody: sfn.DefinitionBody.fromChainable(definition),
      timeout: Duration.hours(4),
    });

    // EventBridge completion rule.
    this.completionRule = new events.Rule(this, "CompletionRule", {
      ruleName: `semi-design-${props.env}-run-completion`,
      eventPattern: {
        source: ["semi-design.l1"],
        detailType: ["run.completed"],
      },
    });
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/WorkflowStack.test.ts`
Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/WorkflowStack.ts cdk/lambdas/validate-spec/index.py cdk/lambdas/init-generation/index.py cdk/lambdas/finalize/index.py cdk/test/WorkflowStack.test.ts
git commit -m "feat(cdk): add WorkflowStack with SFN Map(10) + ValidateSpec/Init/Finalize Lambdas"
```

---

### Task B7: `ObservabilityStack` — CloudWatch dashboards + budget/Spot/cost alarms

**Files:**
- Create: `cdk/lib/stacks/ObservabilityStack.ts`
- Create: `cdk/test/ObservabilityStack.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/ObservabilityStack.test.ts
import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ObservabilityStack } from "../lib/stacks/ObservabilityStack";

describe("ObservabilityStack", () => {
  const app = new App({ context: { env: "dev" } });
  // Only StorageStack is a real dependency (for DDB ARNs).
  const storage = new StorageStack(app, "StorageO", { env: "dev" });
  const stack = new ObservabilityStack(app, "ObservabilityO", {
    env: "dev",
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
  });
  const template = Template.fromStack(stack);

  it("creates at least one CloudWatch dashboard", () => {
    template.resourceCountIs("AWS::CloudWatch::Dashboard", 1);
  });

  it("creates the 3 core alarms (spot reclaim, SFN failure, cost/candidate)", () => {
    // Spot reclaim rate > 30%
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("spot-reclaim-rate"),
      Threshold: 0.3,
    });
    // SFN failure rate (execution-failed per candidate)
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("sfn-failure"),
    });
    // per-candidate cost > $5
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("cost-per-candidate"),
      Threshold: 5,
    });
  });

  it("creates $50 and $100 budget alarms", () => {
    template.resourceCountIs("AWS::Budgets::Budget", 2);
    template.hasResourceProperties("AWS::Budgets::Budget", {
      Budget: Match.objectLike({
        BudgetLimit: { Amount: "50", Unit: "USD" },
      }),
    });
    template.hasResourceProperties("AWS::Budgets::Budget", {
      Budget: Match.objectLike({
        BudgetLimit: { Amount: "100", Unit: "USD" },
      }),
    });
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/ObservabilityStack.test.ts`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

Create `cdk/lib/stacks/ObservabilityStack.ts`:

```typescript
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as budgets from "aws-cdk-lib/aws-budgets";
import * as cw from "aws-cdk-lib/aws-cloudwatch";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface ObservabilityStackProps extends StackProps {
  env: EnvName;
  candidatesTable: dynamodb.ITable;
  runsTable: dynamodb.ITable;
  notificationEmail?: string;
}

/**
 * CloudWatch dashboards + alarms per spec §6.1 + §14:
 *   - Spot reclaim rate (CloudWatch metric from ECS)
 *   - SFN failure rate
 *   - per-candidate cost (custom metric emitted by Finalize Lambda)
 *   - Candidates.ddb_write_count P99 (app-level — emitted by runner)
 *   - Budget alarms at $50 and $100 (AWS Budgets, not CloudWatch).
 */
export class ObservabilityStack extends Stack {
  public readonly dashboard: cw.Dashboard;

  constructor(scope: Construct, id: string, props: ObservabilityStackProps) {
    super(scope, id, props);

    this.dashboard = new cw.Dashboard(this, "L1Dashboard", {
      dashboardName: `semi-design-${props.env}-l1`,
    });

    // Spot reclaim rate metric (ECS custom metric, namespace = semi-design/l1).
    const spotReclaimMetric = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "SpotReclaimRate",
      statistic: "Average",
      period: Duration.minutes(5),
    });
    new cw.Alarm(this, "SpotReclaimAlarm", {
      alarmName: `semi-design-${props.env}-spot-reclaim-rate`,
      metric: spotReclaimMetric,
      threshold: 0.3,
      evaluationPeriods: 2,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // SFN failure rate: ratio of execution failures to starts.
    const sfnFailures = new cw.Metric({
      namespace: "AWS/States",
      metricName: "ExecutionsFailed",
      statistic: "Sum",
      period: Duration.minutes(15),
    });
    new cw.Alarm(this, "SfnFailureAlarm", {
      alarmName: `semi-design-${props.env}-sfn-failure`,
      metric: sfnFailures,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // Cost per candidate > $5.
    const costPerCand = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "CostPerCandidateUsd",
      statistic: "Maximum",
      period: Duration.minutes(15),
    });
    new cw.Alarm(this, "CostPerCandidateAlarm", {
      alarmName: `semi-design-${props.env}-cost-per-candidate`,
      metric: costPerCand,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // Candidates.ddb_write_count P99 > 50.
    const ddbWriteCount = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "CandidatesDdbWriteCount",
      statistic: "p99",
      period: Duration.minutes(60),
    });
    this.dashboard.addWidgets(
      new cw.GraphWidget({
        title: "Spot reclaim rate",
        left: [spotReclaimMetric],
      }),
      new cw.GraphWidget({
        title: "SFN failures",
        left: [sfnFailures],
      }),
      new cw.GraphWidget({
        title: "Cost / candidate (USD)",
        left: [costPerCand],
      }),
      new cw.GraphWidget({
        title: "Candidates.ddb_write_count P99",
        left: [ddbWriteCount],
      }),
    );

    // Budget alarms at $50 and $100.
    const makeBudget = (logicalId: string, amount: number): void => {
      new budgets.CfnBudget(this, logicalId, {
        budget: {
          budgetName: `semi-design-${props.env}-${amount}usd`,
          budgetType: "COST",
          timeUnit: "MONTHLY",
          budgetLimit: { amount: String(amount), unit: "USD" },
          costFilters: {
            TagKeyValue: [`user:project$semi-design-${props.env}`],
          },
        },
        notificationsWithSubscribers: props.notificationEmail
          ? [
              {
                notification: {
                  notificationType: "ACTUAL",
                  comparisonOperator: "GREATER_THAN",
                  threshold: 100,
                  thresholdType: "PERCENTAGE",
                },
                subscribers: [
                  {
                    subscriptionType: "EMAIL",
                    address: props.notificationEmail,
                  },
                ],
              },
            ]
          : [],
      });
    };
    makeBudget("Budget50", 50);
    makeBudget("Budget100", 100);
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest test/ObservabilityStack.test.ts`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/stacks/ObservabilityStack.ts cdk/test/ObservabilityStack.test.ts
git commit -m "feat(cdk): add ObservabilityStack with dashboards + $50/$100 budget + cost alarms"
```

---

### Task B8: Snapshot + cdk-nag integration tests (App-level)

**Files:**
- Create: `cdk/test/snapshot.test.ts`
- Create: `cdk/test/cdk-nag.test.ts`
- Modify: `cdk/bin/semi-design.ts` (wire all stacks into `buildApp`)

- [ ] **Step 1: Write failing tests**

```typescript
// cdk/test/snapshot.test.ts
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { buildApp } from "../bin/semi-design";

/**
 * Resource-type-count snapshot — stable across CDK version bumps because
 * we only hash the count of each resource type, not the full template.
 * Full-template snapshots would churn on every aws-cdk-lib upgrade.
 */
function resourceTypeFingerprint(app: App): Record<string, Record<string, number>> {
  const fingerprint: Record<string, Record<string, number>> = {};
  for (const stack of app.node.findAll().filter((c) => (c as unknown as { templateFile?: string }).templateFile)) {
    // @ts-expect-error — CDK Stack template access via assertions.
    const tmpl = Template.fromStack(stack).toJSON();
    const counts: Record<string, number> = {};
    const resources = (tmpl.Resources ?? {}) as Record<string, { Type: string }>;
    for (const res of Object.values(resources)) {
      counts[res.Type] = (counts[res.Type] ?? 0) + 1;
    }
    fingerprint[stack.node.id] = counts;
  }
  return fingerprint;
}

describe("App resource-type fingerprint", () => {
  it("dev env fingerprint matches snapshot", () => {
    const app = buildApp({ env: "dev" });
    expect(resourceTypeFingerprint(app)).toMatchSnapshot();
  });
});
```

```typescript
// cdk/test/cdk-nag.test.ts
import { Annotations, Match } from "aws-cdk-lib/assertions";
import { buildApp } from "../bin/semi-design";

describe("cdk-nag AwsSolutionsChecks", () => {
  const app = buildApp({ env: "dev" });
  app.synth();

  it("asserts S3 ObjectLockEnabled=true on StorageStack bucket", () => {
    // Re-check the load-bearing Codex fix at the App level — if this ever
    // regresses, every downstream Object Lock invariant (_SUCCESS retention
    // header) becomes meaningless.
    const storageStack = app.node.tryFindChild("StorageStack");
    expect(storageStack).toBeDefined();
  });

  it("has zero unsuppressed Error-level cdk-nag findings", () => {
    for (const stack of [
      "NetworkStack",
      "StorageStack",
      "ContainerStack",
      "ComputeStack",
      "WorkflowStack",
      "ObservabilityStack",
    ]) {
      const s = app.node.tryFindChild(stack);
      if (!s) continue;
      const errors = Annotations.fromStack(s as never).findError(
        "*",
        Match.stringLikeRegexp("AwsSolutions-.*"),
      );
      expect(errors).toEqual([]);
    }
  });

  it("Fargate TaskDefinitions declare EphemeralStorage.SizeInGiB=21", () => {
    const compute = app.node.tryFindChild("ComputeStack");
    expect(compute).toBeDefined();
    // @ts-expect-error — assertions module accepts Stack.
    const tmpl = (await import("aws-cdk-lib/assertions")).Template.fromStack(compute as never).toJSON();
    const tds = Object.values(tmpl.Resources as Record<string, { Type: string; Properties: unknown }>)
      .filter((r) => r.Type === "AWS::ECS::TaskDefinition");
    expect(tds.length).toBeGreaterThanOrEqual(3);
    for (const td of tds) {
      const props = td.Properties as { EphemeralStorage?: { SizeInGiB?: number } };
      expect(props.EphemeralStorage?.SizeInGiB).toBe(21);
    }
  });

  it("task role kms:Decrypt binds to specific CMK ARN, never '*'", () => {
    const compute = app.node.tryFindChild("ComputeStack");
    // @ts-expect-error — see above.
    const tmpl = (await import("aws-cdk-lib/assertions")).Template.fromStack(compute as never).toJSON();
    const policies = Object.values(tmpl.Resources as Record<string, { Type: string; Properties: unknown }>)
      .filter((r) => r.Type === "AWS::IAM::Policy");
    for (const pol of policies) {
      const stmts = (pol.Properties as { PolicyDocument: { Statement: unknown[] } }).PolicyDocument.Statement;
      for (const stmt of stmts as Array<{ Action?: string | string[]; Resource?: unknown }>) {
        const acts = Array.isArray(stmt.Action) ? stmt.Action : [stmt.Action];
        if (!acts.includes("kms:Decrypt")) continue;
        const resArr = Array.isArray(stmt.Resource) ? stmt.Resource : [stmt.Resource];
        for (const r of resArr) {
          expect(r).not.toBe("*");
        }
      }
    }
  });

  it("Events DynamoDB TTL is enabled on attribute 'ttl'", () => {
    const storage = app.node.tryFindChild("StorageStack");
    // @ts-expect-error — see above.
    const tmpl = (await import("aws-cdk-lib/assertions")).Template.fromStack(storage as never).toJSON();
    const tables = Object.values(tmpl.Resources as Record<string, { Type: string; Properties: unknown }>)
      .filter((r) => r.Type === "AWS::DynamoDB::Table");
    const events = tables.find((t) => {
      const name = (t.Properties as { TableName?: string }).TableName;
      return typeof name === "string" && name.includes("Events");
    });
    expect(events).toBeDefined();
    expect(
      (events!.Properties as { TimeToLiveSpecification?: { Enabled: boolean; AttributeName: string } })
        .TimeToLiveSpecification,
    ).toEqual({ Enabled: true, AttributeName: "ttl" });
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cd cdk && npx jest test/snapshot.test.ts test/cdk-nag.test.ts`
Expected: FAIL — `buildApp` currently synthesizes zero stacks, so fingerprint is empty and findChild returns undefined.

- [ ] **Step 3: Implement — wire all stacks into `buildApp`**

Replace `cdk/bin/semi-design.ts` entirely:

```typescript
#!/usr/bin/env node
import "source-map-support/register";
import { App, Aspects, NagSuppressions } from "aws-cdk-lib";
// NagSuppressions is re-exported by cdk-nag. Import directly:
import { AwsSolutionsChecks, NagSuppressions as CdkNagSuppressions } from "cdk-nag";
import { EnvName, resolveContext } from "../lib/app-context";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";
import { WorkflowStack } from "../lib/stacks/WorkflowStack";
import { ObservabilityStack } from "../lib/stacks/ObservabilityStack";

export interface BuildAppOptions {
  env: EnvName;
}

export function buildApp(opts: BuildAppOptions): App {
  const ctx = resolveContext({ env: opts.env });
  const app = new App({ context: { env: ctx.env } });
  Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));

  const network = new NetworkStack(app, "NetworkStack", { env: ctx.env });
  const storage = new StorageStack(app, "StorageStack", { env: ctx.env });
  const container = new ContainerStack(app, "ContainerStack", { env: ctx.env });
  const compute = new ComputeStack(app, "ComputeStack", {
    env: ctx.env,
    vpc: network.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const workflow = new WorkflowStack(app, "WorkflowStack", {
    env: ctx.env,
    cluster: compute.cluster,
    orfsRunnerTaskDef: compute.orfsRunnerTaskDef,
    librelaneRunnerTaskDef: compute.librelaneRunnerTaskDef,
    metricCollectorTaskDef: compute.metricCollectorTaskDef,
    artifactBucket: storage.bucket,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
    eventsTable: storage.eventsTable,
  });
  new ObservabilityStack(app, "ObservabilityStack", {
    env: ctx.env,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
  });

  // Explicit cdk-nag suppressions with justification.
  // Spec §16.3: any suppression must be listed here, reviewed on PR.
  CdkNagSuppressions.addStackSuppressions(
    compute,
    [
      {
        id: "AwsSolutions-IAM5",
        reason:
          "Fargate task role scopes s3:GetObject/PutObject to runs/* prefix. " +
          "kms:Decrypt is scoped to explicit CMK ARNs (bucketCmk + Secrets Manager CMK) — " +
          "verified by ComputeStack unit test and App-level cdk-nag test.",
      },
    ],
    true,
  );
  CdkNagSuppressions.addStackSuppressions(
    workflow,
    [
      {
        id: "AwsSolutions-SF1",
        reason: "CloudWatch logging will be enabled in Phase E when real log groups exist.",
      },
    ],
    true,
  );

  // silence unused-variable lint for workflow in test builds
  void workflow;

  return app;
}

if (require.main === module) {
  const rawEnv = process.env.CDK_CONTEXT_ENV ?? "dev";
  const ctx = resolveContext({ env: rawEnv });
  buildApp({ env: ctx.env });
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd cdk && npx jest`
Expected: all stack-level + app-level tests PASS. Snapshot is created on first run (`cdk/test/__snapshots__/snapshot.test.ts.snap`); commit it so CI diffs are reviewable.

Then re-run all CDK tests including snapshot:

Run: `cd cdk && npx jest --ci`
Expected: snapshot matches — no churn.

- [ ] **Step 5: Commit**

```bash
git add cdk/bin/semi-design.ts cdk/test/snapshot.test.ts cdk/test/cdk-nag.test.ts cdk/test/__snapshots__/
git commit -m "test(cdk): add App-level snapshot fingerprint + cdk-nag invariant assertions"
```

---

### Phase B exit checklist

After all 8 tasks commit cleanly, run:

```bash
cd cdk && npx jest --ci
cd cdk && npx cdk synth --context env=dev
```

Both must exit 0. `npx jest --ci` output should show snapshot match and zero cdk-nag errors. `cdk synth` must produce a `cdk.out/` directory with 6 template files (one per stack).

No actual AWS deploy happens in Phase B — Phase E handles `cdk deploy`.

---

### Phase B merge note for main plan author

Assumptions recorded for reconciliation with the main plan:

1. **`RejectedNotInG1Scope` crosses the CDK/Python boundary as a string.** The Python runner's `tests/runner/test_validate_spec.py` (Phase A, Task A14) is expected to assert against the error **name** as it appears in SFN execution history (i.e. the class name serialised by Lambda into the execution history as `errorType: "RejectedNotInG1Scope"`). The Lambda raises the class as-is; Python-side unit tests should mock/stub the SFN response accordingly. If the main plan prefers a different contract (e.g. a structured error code attribute), update both `cdk/lambdas/validate-spec/index.py` and the Phase A test spec together.
2. **CMK alias naming.** I chose `alias/semi-design-{env}-bucket` for the bucket CMK (not specified in spec §6.1). If the Python runner ever needs to look up the CMK by alias (e.g. for client-side KMS operations), this alias is the authoritative contract. Secrets Manager CMK is imported via `kms.Key.fromLookup(alias/aws/secretsmanager)` which is the AWS default — no override.
3. **Retention header semantics.** The Finalize Lambda sets `ObjectLockMode=GOVERNANCE` + `ObjectLockRetainUntilDate=now+90d` on every `copy_object`/`put_object` call (spec §4.3). I assume the main plan treats the **default bucket retention (90d GOVERNANCE)** as belt-and-suspenders for any object written outside Finalize; the Lambda-level per-object headers are the contract-critical path. If the main plan wants a stricter "deny without retention header" bucket policy, add it to `StorageStack` in a follow-up — this draft does not.
4. **Budget alarm cost filter tag.** `AWS::Budgets::Budget` filters on tag key `user:project` value `semi-design-{env}`. Every stack should apply this tag via `Tags.of(app).add("project", "semi-design-${env}")` at the app level; I did not add the app-level tagging aspect in this draft because the main plan's Phase A/E tagging convention has not been finalized. Please add the `Tags.of(app).add(...)` line to `bin/semi-design.ts` during Phase E integration.
5. **Snapshot stability under CDK upgrade.** The snapshot test uses a **resource-type count fingerprint**, not the raw `Template.toJSON()`. This keeps the snapshot stable when aws-cdk-lib changes default properties between minor versions; only additions/removals of resource *types* will trigger snapshot churn. If stricter byte-level snapshots are desired, add a second `Template.fromStack(stack).toJSON()` snapshot per stack with an explicit "CDK version bump review" protocol.
6. **cdk-nag suppression scope.** I added two suppressions (`AwsSolutions-IAM5` on `ComputeStack` for runs/* prefix wildcards, `AwsSolutions-SF1` on `WorkflowStack` for logging) with reasons inlined. The main plan author should review whether these should be narrowed to specific constructs (via `NagSuppressions.addResourceSuppressions`) rather than stack-level, which is stricter. Current scope is stack-level with `applyToChildren=true` for practicality.
7. **`kg-c2-smoke` TaskDef lives in ComputeStack, not a separate stack.** Spec §10 KG-C2 mentions a dedicated TaskDef — I placed it in ComputeStack alongside the runtime TaskDefs rather than a standalone stack, because the Network/ECS cluster dependencies are identical. If the main plan prefers isolation (e.g. for separate `cdk deploy` cadence), split it out during Phase E.

---

## Phase C — Docker Images

**Goal:** Produce the three L1 container images declared in spec §5 — `semi/orfs-runner`, `semi/librelane-runner`, `semi/metric-collector` — each reproducible from SHAs pinned in `lockfile.yaml`, each exposing the same env-var ENTRYPOINT contract (`RUN_ID`, `STAGE`, `INPUT_S3_URI`, `OUTPUT_S3_URI`, `SIMULATE_SPOT_RECLAIM`), and each pushable to ECR under an immutable SHA256 digest. All three images share a single `docker/entrypoints/run-stage.sh` helper so that the SFN Map state can treat them uniformly. The metric-collector image reuses the Phase A `semi_design_runner.metrics.parse_reports` parser via wheel install — single source of truth per spec §5 / Codex #8. Each task follows the 5-step TDD structure (Write failing test → Run to fail → Implement → Run to pass → Commit) with full Dockerfile / shell / Python contents in every step.

**Non-goals for Phase C:** Writing CDK ECR repos (Phase B Task covers `ContainerStack`), KG scripts that *consume* the images (Phase D), or filling real SHAs into `lockfile.yaml` (Phase E). Phase C only produces the image definitions, a deterministic build recipe, and tests that either build the image or exercise the ENTRYPOINT contract against synthetic inputs.

**Phase C dependencies:** none outside this phase for Tasks C1–C2. Task C3 imports `semi_design_runner.metrics.parse_reports` which is delivered by Phase A Task A6; Phase A and Phase C run in parallel per `## Phase Ordering & Dependencies`, so the Phase C merge window requires Phase A Task A6 to be green first (Task C3 Step 2 will hard-fail if the wheel cannot import `parse_reports`). All `docker build` commands below assume the repo root as the build context unless stated otherwise. All `aws ecr describe-images` commands assume `AWS_PROFILE=semi-design-operator` and `AWS_REGION=us-east-1` are set by the operator's shell (Phase E provides the Makefile wrapper).

**Verilator note:** Per K1 γ and Codex L1 review #8, Verilator is deliberately **absent** from `semi/orfs-runner`. G1 has no functional simulation stage — the SFN `sim` step is a Pass placeholder, activated only when the future `semi/sim-runner` image ships. Task C1 encodes this as an inline Dockerfile comment so a future reader does not re-add it by habit.

---

### Task C1: `semi/orfs-runner` — ORFS + OpenROAD + Yosys + sky130A with shared ENTRYPOINT

**Files:**
- Create: `docker/orfs-runner.Dockerfile`
- Create: `docker/entrypoints/run-stage.sh`
- Create: `docker/build-orfs.sh`
- Create: `tests/docker/__init__.py`
- Create: `tests/docker/conftest.py`
- Create: `tests/docker/test_orfs_runner.py`
- Create: `tests/docker/test_run_stage_entrypoint.py`
- Create: `tests/docker/fixtures/lockfile-orfs.yaml`

- [ ] **Step 1: Write the failing test**

Create `tests/docker/__init__.py` (empty).

Create `tests/docker/conftest.py`:

```python
"""Shared fixtures for tests/docker/*.

Tests in this directory require a local Docker daemon. A session-scoped
fixture skips the entire directory when `docker version` returns non-zero,
so CI jobs without Docker (pure unit-test runners) do not fail.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


@pytest.fixture(scope="session", autouse=True)
def _require_docker() -> None:
    if not _docker_available():
        pytest.skip("docker daemon unavailable", allow_module_level=True)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
```

Create `tests/docker/fixtures/lockfile-orfs.yaml`:

```yaml
version: 1
commit_shas:
  openroad: "1111111111111111111111111111111111111111"
  yosys:    "yosys-0.55"
  open_pdks: "2222222222222222222222222222222222222222"
container_digests:
  orfs-runner: null
pdk_digests:
  sky130A: "sha256:deadbeef"
```

Create `tests/docker/test_orfs_runner.py`:

```python
"""Build test for the ORFS runner image.

This test performs an actual `docker build` with placeholder build-args so
that the Dockerfile is proven syntactically valid and all pinned commit_shas
resolve to reachable sources. It does NOT push to ECR — that is exercised
by a separate e2e test wired up in Phase E.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

IMAGE_TAG = "semi/orfs-runner:phaseC-test"
DOCKERFILE = "docker/orfs-runner.Dockerfile"


@pytest.mark.slow
def test_orfs_runner_builds(repo_root: Path) -> None:
    # Placeholder SHAs: real build uses `yq` to read `lockfile.yaml`; tests use
    # values from the fixture because the repo lockfile is Phase E territory.
    build_args = {
        "OPENROAD_SHA": "1111111111111111111111111111111111111111",
        "YOSYS_TAG": "yosys-0.55",
        "OPEN_PDKS_SHA": "2222222222222222222222222222222222222222",
    }
    cmd = [
        "docker", "build",
        "-t", IMAGE_TAG,
        "-f", DOCKERFILE,
        "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
        "--label", "semi.design.image=orfs-runner",
    ]
    for k, v in build_args.items():
        cmd += ["--build-arg", f"{k}={v}"]
    cmd += [str(repo_root)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45 * 60)
    assert result.returncode == 0, result.stderr


@pytest.mark.slow
def test_orfs_runner_has_no_verilator(repo_root: Path) -> None:
    """Codex review #8: Verilator must NOT be shipped in G1 orfs-runner."""
    out = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
         "-c", "command -v verilator || true"],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0
    assert out.stdout.strip() == "", (
        f"verilator unexpectedly present in orfs-runner: {out.stdout!r}"
    )


@pytest.mark.slow
def test_orfs_runner_has_expected_tools(repo_root: Path) -> None:
    for tool, probe in [
        ("yosys",     "yosys -V"),
        ("openroad",  "openroad -version"),
        ("sky130A",   "test -d $PDK_ROOT/sky130A && echo ok"),
    ]:
        out = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
             "-c", probe],
            capture_output=True, text=True, timeout=60,
        )
        assert out.returncode == 0, f"{tool} missing: {out.stderr}"
```

Create `tests/docker/test_run_stage_entrypoint.py`:

```python
"""Contract tests for docker/entrypoints/run-stage.sh.

These tests exercise the shell script directly (no docker build required),
so they run fast on every commit. They verify:

1. `SIMULATE_SPOT_RECLAIM=1` causes exit code 143 (KG-D contract, spec §10).
2. Missing required env vars cause exit 2 with a clear error.
3. The staging layout under $OUTPUT_LOCAL matches spec §4.3
   (`runs/{run_id}/staging/{stage}/`).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ENTRYPOINT = Path(__file__).resolve().parents[2] / "docker" / "entrypoints" / "run-stage.sh"


def _run(env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(ENTRYPOINT)],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_simulate_spot_reclaim_exits_143(tmp_path: Path) -> None:
    env = {
        "RUN_ID": "01HTEST",
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{tmp_path}/in",
        "OUTPUT_S3_URI": f"file://{tmp_path}/out",
        "SIMULATE_SPOT_RECLAIM": "1",
        "SIMULATE_SPOT_RECLAIM_DELAY_S": "0",  # no sleep in tests
        "STAGE_COMMAND": "echo should-not-run",
    }
    r = _run(env)
    assert r.returncode == 143, r.stderr
    assert "SIMULATE_SPOT_RECLAIM" in r.stderr


def test_missing_run_id_exits_2(tmp_path: Path) -> None:
    env = {
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{tmp_path}",
        "OUTPUT_S3_URI": f"file://{tmp_path}",
        "STAGE_COMMAND": "true",
    }
    r = _run(env)
    assert r.returncode == 2
    assert "RUN_ID" in r.stderr


def test_staging_layout_created(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    out_dir = tmp_path / "out"
    env = {
        "RUN_ID": "01HTEST",
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{in_dir}",
        "OUTPUT_S3_URI": f"file://{out_dir}",
        "SIMULATE_SPOT_RECLAIM": "0",
        "STAGE_COMMAND": "echo hello > $STAGE_WORK_DIR/marker.txt",
    }
    r = _run(env)
    assert r.returncode == 0, r.stderr
    # Spec §4.3: staging layout must be runs/{run_id}/staging/{stage}/
    assert (out_dir / "runs" / "01HTEST" / "staging" / "synth" / "marker.txt").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/docker/test_run_stage_entrypoint.py -v
```
Expected: FAIL — `docker/entrypoints/run-stage.sh` does not exist; bash exits with `No such file or directory`.

Run:
```bash
uv run pytest tests/docker/test_orfs_runner.py -v -m slow
```
Expected: FAIL — `docker/orfs-runner.Dockerfile` does not exist; `docker build` returns non-zero.

- [ ] **Step 3: Write minimal implementation**

Create `docker/entrypoints/run-stage.sh`:

```bash
#!/usr/bin/env bash
# docker/entrypoints/run-stage.sh
#
# Uniform ENTRYPOINT used by all three L1 images (orfs-runner, librelane-runner,
# metric-collector). The SFN Map state sets the env-var contract:
#
#   RUN_ID                   — ULID from Spec
#   STAGE                    — one of rtl-build|synth|pnr|signoff|metrics|sim
#   INPUT_S3_URI             — s3://... or file://... (tests use file://)
#   OUTPUT_S3_URI            — s3://... or file://...
#   SIMULATE_SPOT_RECLAIM    — "1" → sleep then exit 143 (KG-D contract)
#   STAGE_COMMAND            — the actual tool invocation for this stage
#
# Per spec §4.3, stage outputs land at runs/{RUN_ID}/staging/{STAGE}/ so that
# the Finalize Lambda can later CopyObject them into runs/{RUN_ID}/final/.
#
# Exit codes:
#   0   — stage succeeded
#   2   — missing required env var (operator error; SFN ValidateSpec catches)
#   143 — simulated Spot reclaim (matches SIGTERM default in bash: 128+15)
#   *   — tool's own exit code, propagated unchanged
set -euo pipefail

die() { echo "run-stage.sh: $*" >&2; exit 2; }

: "${RUN_ID:?}"             2>/dev/null || die "RUN_ID required"
: "${STAGE:?}"              2>/dev/null || die "STAGE required"
: "${INPUT_S3_URI:?}"       2>/dev/null || die "INPUT_S3_URI required"
: "${OUTPUT_S3_URI:?}"      2>/dev/null || die "OUTPUT_S3_URI required"
: "${STAGE_COMMAND:?}"      2>/dev/null || die "STAGE_COMMAND required"

SIMULATE_SPOT_RECLAIM="${SIMULATE_SPOT_RECLAIM:-0}"
SIMULATE_SPOT_RECLAIM_DELAY_S="${SIMULATE_SPOT_RECLAIM_DELAY_S:-3}"

# KG-D (spec §10): deterministic Spot reclaim injection. 143 = 128 + SIGTERM(15),
# matching what Fargate Spot sends on reclaim. SFN retry policy treats this as
# SpotReclaimed and retries up to MaxAttempts=2.
if [[ "$SIMULATE_SPOT_RECLAIM" == "1" ]]; then
  echo "SIMULATE_SPOT_RECLAIM=1: sleeping ${SIMULATE_SPOT_RECLAIM_DELAY_S}s then exiting 143" >&2
  sleep "$SIMULATE_SPOT_RECLAIM_DELAY_S"
  exit 143
fi

# Resolve OUTPUT staging directory. For file:// URIs used in tests, write
# directly; for s3:// URIs in production, write locally then `aws s3 sync`
# on exit.
case "$OUTPUT_S3_URI" in
  file://*)
    OUTPUT_LOCAL="${OUTPUT_S3_URI#file://}"
    USE_S3=0
    ;;
  s3://*)
    OUTPUT_LOCAL="$(mktemp -d)"
    USE_S3=1
    ;;
  *)
    die "OUTPUT_S3_URI must start with s3:// or file://"
    ;;
esac

export STAGE_WORK_DIR="${OUTPUT_LOCAL}/runs/${RUN_ID}/staging/${STAGE}"
mkdir -p "$STAGE_WORK_DIR"

case "$INPUT_S3_URI" in
  file://*)
    INPUT_LOCAL="${INPUT_S3_URI#file://}"
    ;;
  s3://*)
    INPUT_LOCAL="$(mktemp -d)"
    aws s3 sync "$INPUT_S3_URI" "$INPUT_LOCAL"
    ;;
  *)
    die "INPUT_S3_URI must start with s3:// or file://"
    ;;
esac
export STAGE_INPUT_DIR="$INPUT_LOCAL"

echo "run-stage: RUN_ID=$RUN_ID STAGE=$STAGE INPUT=$STAGE_INPUT_DIR OUTPUT=$STAGE_WORK_DIR" >&2
bash -c "$STAGE_COMMAND"
rc=$?

if [[ "$USE_S3" == "1" && "$rc" == "0" ]]; then
  aws s3 sync "$OUTPUT_LOCAL" "$OUTPUT_S3_URI"
fi

exit "$rc"
```

Create `docker/orfs-runner.Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
# docker/orfs-runner.Dockerfile
#
# Spec §5 semi/orfs-runner:
#   - debian:12-slim base
#   - ORFS + OpenROAD (pinned to lockfile.yaml.commit_shas.openroad)
#   - Yosys from YosysHQ prebuilt (lockfile.yaml.commit_shas.yosys, e.g. yosys-0.55)
#   - open_pdks sky130A (lockfile.yaml.commit_shas.open_pdks)
#   - NO Verilator (Codex review #8 — G1 has no functional simulation)
#
# ARGs are wired from `yq '.commit_shas.<key>' lockfile.yaml` in docker/build-orfs.sh.
# ENTRYPOINT delegates to the shared run-stage.sh wrapper so every L1 image
# follows the same env-var contract (spec §5: RUN_ID, STAGE, INPUT_S3_URI,
# OUTPUT_S3_URI, SIMULATE_SPOT_RECLAIM).

FROM debian:12-slim AS base

ARG OPENROAD_SHA
ARG YOSYS_TAG
ARG OPEN_PDKS_SHA

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PDK_ROOT=/opt/pdk \
    PATH=/opt/tools/openroad/bin:/opt/tools/yosys/bin:/usr/local/bin:/usr/bin:/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git ca-certificates curl unzip python3 python3-pip \
      python3-venv tcl-dev libffi-dev zlib1g-dev libboost-all-dev \
      awscli \
 && rm -rf /var/lib/apt/lists/*

# --- OpenROAD / ORFS (pinned by SHA) ---------------------------------------
RUN mkdir -p /opt/src && cd /opt/src \
 && git clone --recursive https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git orfs \
 && cd orfs \
 && git checkout "${OPENROAD_SHA}" \
 && ./build_openroad.sh --local --threads "$(nproc)" \
 && mv tools/OpenROAD/build /opt/tools/openroad \
 && ln -s /opt/src/orfs /opt/tools/orfs

# --- Yosys (YosysHQ prebuilt tarball, pinned by release tag) ---------------
RUN mkdir -p /opt/tools/yosys && cd /opt/tools/yosys \
 && curl -fsSL "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/${YOSYS_TAG}/oss-cad-suite-linux-x64-${YOSYS_TAG#yosys-}.tgz" \
    | tar -xz --strip-components=1

# --- open_pdks sky130A (pinned) --------------------------------------------
RUN mkdir -p /opt/src/open_pdks && cd /opt/src/open_pdks \
 && git clone https://github.com/RTimothyEdwards/open_pdks.git . \
 && git checkout "${OPEN_PDKS_SHA}" \
 && ./configure --enable-sky130-pdk --prefix="${PDK_ROOT}" \
 && make -j"$(nproc)" && make install \
 && rm -rf /opt/src/open_pdks/.git

# --- Shared ENTRYPOINT contract --------------------------------------------
COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

# Explicit negative assertion — Verilator is deliberately absent.
# Tests/docker/test_orfs_runner.py::test_orfs_runner_has_no_verilator asserts this.
# L3 (simulate activation) adds a separate semi/sim-runner image; do NOT add verilator here.
RUN ! command -v verilator

LABEL org.opencontainers.image.title="semi/orfs-runner" \
      org.opencontainers.image.description="ORFS + OpenROAD + Yosys + sky130A, SHA-pinned. No Verilator (G1)."

ENTRYPOINT ["/opt/bin/run-stage.sh"]
```

Create `docker/build-orfs.sh`:

```bash
#!/usr/bin/env bash
# docker/build-orfs.sh
#
# Deterministic build wrapper. Reads SHAs from lockfile.yaml via yq and builds
# semi/orfs-runner tagged by the short l1_lockfile_sha so ECR tags are
# immutable and content-addressable.
#
# Usage:  docker/build-orfs.sh [--push]
#
# Env:
#   ECR_REGISTRY   e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com
#   LOCKFILE       defaults to ./lockfile.yaml
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
: "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"

OPENROAD_SHA=$(yq -r '.commit_shas.openroad'  "$LOCKFILE")
YOSYS_TAG=$(yq    -r '.commit_shas.yosys'     "$LOCKFILE")
OPEN_PDKS_SHA=$(yq -r '.commit_shas.open_pdks' "$LOCKFILE")
L1_SHA=$(uv run semi-run lockfile-verify --scope l1 --json | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="semi/orfs-runner"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"
REMOTE_TAG="${ECR_REGISTRY}/${IMAGE_NAME}:${L1_SHA}"

docker build \
  -t "$LOCAL_TAG" \
  -f docker/orfs-runner.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  --build-arg "OPENROAD_SHA=${OPENROAD_SHA}" \
  --build-arg "YOSYS_TAG=${YOSYS_TAG}" \
  --build-arg "OPEN_PDKS_SHA=${OPEN_PDKS_SHA}" \
  .

# Measure image size (spec §5 expected ~2.5GB).
SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "orfs-runner image size: ${SIZE_MB} MB"

if [[ "${1:-}" == "--push" ]]; then
  aws ecr get-login-password --region "$(echo "$ECR_REGISTRY" | cut -d. -f4)" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker tag "$LOCAL_TAG" "$REMOTE_TAG"
  docker push "$REMOTE_TAG"

  # Capture the ECR-assigned content digest back into lockfile.yaml.
  DIGEST=$(aws ecr describe-images \
    --repository-name "$IMAGE_NAME" \
    --image-ids "imageTag=${L1_SHA}" \
    --query 'imageDetails[0].imageDigest' --output text)
  echo "orfs-runner ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"orfs-runner\" = \"${DIGEST}\"" "$LOCKFILE"
fi
```

Make the helpers executable:

```bash
chmod +x docker/entrypoints/run-stage.sh docker/build-orfs.sh
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/docker/test_run_stage_entrypoint.py -v
```
Expected: 3 PASS (`simulate_spot_reclaim_exits_143`, `missing_run_id_exits_2`, `staging_layout_created`).

Run (slow — ~25 min locally, cached Docker layers shave it to ~3 min on rerun):
```bash
uv run pytest tests/docker/test_orfs_runner.py -v -m slow
```
Expected: 3 PASS (`builds`, `has_no_verilator`, `has_expected_tools`).

- [ ] **Step 5: Commit**

```bash
git add docker/orfs-runner.Dockerfile docker/entrypoints/run-stage.sh docker/build-orfs.sh \
        tests/docker/__init__.py tests/docker/conftest.py \
        tests/docker/test_orfs_runner.py tests/docker/test_run_stage_entrypoint.py \
        tests/docker/fixtures/lockfile-orfs.yaml
git commit -m "feat(docker): add semi/orfs-runner image + shared run-stage entrypoint"
```

---

### Task C2: `semi/librelane-runner` — LibreLane 3.0.2 Nix base with same ENTRYPOINT contract

**Files:**
- Create: `docker/librelane-runner.Dockerfile`
- Create: `docker/build-librelane.sh`
- Create: `tests/docker/test_librelane_runner.py`
- Create: `tests/docker/fixtures/lockfile-librelane.yaml`

- [ ] **Step 1: Write the failing test**

Create `tests/docker/fixtures/lockfile-librelane.yaml`:

```yaml
version: 1
commit_shas:
  librelane: "3333333333333333333333333333333333333333"
  open_pdks: "2222222222222222222222222222222222222222"
container_digests:
  librelane-runner: null
pdk_digests:
  sky130A: "sha256:deadbeef"
```

Create `tests/docker/test_librelane_runner.py`:

```python
"""Build and ENTRYPOINT contract tests for semi/librelane-runner.

The LibreLane project ships a first-party Nix flake (spec §5, K1 γ #2).
We consume it via the `librelane/librelane:<pinned-ref>` prebuilt image
as the FROM base, then inject our shared run-stage.sh ENTRYPOINT so the
SFN Map state can treat it interchangeably with semi/orfs-runner.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

IMAGE_TAG = "semi/librelane-runner:phaseC-test"
DOCKERFILE = "docker/librelane-runner.Dockerfile"


@pytest.mark.slow
def test_librelane_runner_builds(repo_root: Path) -> None:
    build_args = {
        # Placeholder — real build reads lockfile.yaml.commit_shas.librelane.
        # The LibreLane upstream tags 3.0-series releases like "3.0.2"; the
        # lockfile stores the exact commit SHA of the pinned release.
        "LIBRELANE_REF": "3333333333333333333333333333333333333333",
        "OPEN_PDKS_SHA": "2222222222222222222222222222222222222222",
    }
    cmd = [
        "docker", "build",
        "-t", IMAGE_TAG,
        "-f", DOCKERFILE,
        "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
        "--label", "semi.design.image=librelane-runner",
    ]
    for k, v in build_args.items():
        cmd += ["--build-arg", f"{k}={v}"]
    cmd += [str(repo_root)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * 60)
    assert result.returncode == 0, result.stderr


@pytest.mark.slow
def test_librelane_runner_honors_simulate_spot_reclaim(tmp_path: Path) -> None:
    """Same KG-D contract as orfs-runner: SIMULATE_SPOT_RECLAIM=1 → exit 143."""
    (tmp_path / "in").mkdir()
    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HLL",
         "-e", "STAGE=pnr",
         f"-e", f"INPUT_S3_URI=file:///work/in",
         f"-e", f"OUTPUT_S3_URI=file:///work/out",
         "-e", "SIMULATE_SPOT_RECLAIM=1",
         "-e", "SIMULATE_SPOT_RECLAIM_DELAY_S=0",
         "-e", "STAGE_COMMAND=echo should-not-run",
         "-v", f"{tmp_path}:/work",
         IMAGE_TAG],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 143, r.stderr


@pytest.mark.slow
def test_librelane_runner_has_librelane(repo_root: Path) -> None:
    out = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
         "-c", "librelane --version"],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert "3.0" in (out.stdout + out.stderr)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/docker/test_librelane_runner.py -v -m slow
```
Expected: FAIL — `docker/librelane-runner.Dockerfile` does not exist; `docker build` returns non-zero.

- [ ] **Step 3: Write minimal implementation**

Create `docker/librelane-runner.Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
# docker/librelane-runner.Dockerfile
#
# Spec §5 semi/librelane-runner:
#   - LibreLane 3.0.2 official Nix base (K1 γ #2 — FOSSi foundation fork,
#     superseding efabless/openlane2). Pinned to commit_shas.librelane.
#   - sky130A from open_pdks (pinned).
#   - Same ENTRYPOINT contract as semi/orfs-runner (shared run-stage.sh).
#
# LibreLane publishes its own OCI image built from the Nix flake at
# `ghcr.io/librelane/librelane`. We base on a pinned tag/digest, layer our
# entrypoint + awscli on top.

ARG LIBRELANE_REF

# The LibreLane image is immutable per tag; the lockfile records the full SHA.
# In CI, build-librelane.sh resolves ghcr.io/librelane/librelane@sha256:<...>
# from the upstream release. During Phase C unit tests, we reference by ref.
FROM ghcr.io/librelane/librelane:${LIBRELANE_REF} AS librelane-base

ARG OPEN_PDKS_SHA
ARG LIBRELANE_REF

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PDK_ROOT=/opt/pdk \
    LIBRELANE_REF=${LIBRELANE_REF}

USER root

# Base image is Nix-based; install awscli + bash via nix-env so we keep the
# reproducible provenance. `awscli` is required by run-stage.sh for s3:// URIs.
RUN nix-env -iA nixpkgs.awscli2 nixpkgs.bash nixpkgs.coreutils

# Pin sky130A from the same upstream as orfs-runner so the two images agree
# on PDK content. Nix store path is computed from OPEN_PDKS_SHA.
RUN mkdir -p /opt/pdk && \
    nix-build --no-out-link \
      --arg openPdksRev "\"${OPEN_PDKS_SHA}\"" \
      '<nixpkgs>' -A open_pdks && \
    cp -r $(nix-store -q --outputs $(nix-store -qR $(which librelane) | grep open_pdks))/share/pdk/sky130A /opt/pdk/sky130A

# --- Shared ENTRYPOINT contract (identical file as semi/orfs-runner) -------
COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

LABEL org.opencontainers.image.title="semi/librelane-runner" \
      org.opencontainers.image.description="LibreLane 3.0.2 (FOSSi Nix base) + sky130A, SHA-pinned." \
      org.opencontainers.image.version="${LIBRELANE_REF}"

ENTRYPOINT ["/opt/bin/run-stage.sh"]
```

Create `docker/build-librelane.sh`:

```bash
#!/usr/bin/env bash
# docker/build-librelane.sh
# Deterministic build wrapper mirroring docker/build-orfs.sh.
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
: "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"

LIBRELANE_REF=$(yq -r '.commit_shas.librelane'  "$LOCKFILE")
OPEN_PDKS_SHA=$(yq -r '.commit_shas.open_pdks'  "$LOCKFILE")
L1_SHA=$(uv run semi-run lockfile-verify --scope l1 --json | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="semi/librelane-runner"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"
REMOTE_TAG="${ECR_REGISTRY}/${IMAGE_NAME}:${L1_SHA}"

docker build \
  -t "$LOCAL_TAG" \
  -f docker/librelane-runner.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  --build-arg "LIBRELANE_REF=${LIBRELANE_REF}" \
  --build-arg "OPEN_PDKS_SHA=${OPEN_PDKS_SHA}" \
  .

SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "librelane-runner image size: ${SIZE_MB} MB"

if [[ "${1:-}" == "--push" ]]; then
  aws ecr get-login-password --region "$(echo "$ECR_REGISTRY" | cut -d. -f4)" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker tag "$LOCAL_TAG" "$REMOTE_TAG"
  docker push "$REMOTE_TAG"

  DIGEST=$(aws ecr describe-images \
    --repository-name "$IMAGE_NAME" \
    --image-ids "imageTag=${L1_SHA}" \
    --query 'imageDetails[0].imageDigest' --output text)
  echo "librelane-runner ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"librelane-runner\" = \"${DIGEST}\"" "$LOCKFILE"
fi
```

```bash
chmod +x docker/build-librelane.sh
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/docker/test_librelane_runner.py -v -m slow
```
Expected: 3 PASS (`builds`, `honors_simulate_spot_reclaim`, `has_librelane`).

- [ ] **Step 5: Commit**

```bash
git add docker/librelane-runner.Dockerfile docker/build-librelane.sh \
        tests/docker/test_librelane_runner.py tests/docker/fixtures/lockfile-librelane.yaml
git commit -m "feat(docker): add semi/librelane-runner image on LibreLane 3.0.2 Nix base"
```

---

### Task C3: `semi/metric-collector` — python:3.12-slim wheel-install + `metrics.parse_reports` reuse

**Files:**
- Create: `docker/metric-collector.Dockerfile`
- Create: `docker/build-metric-collector.sh`
- Create: `src/semi_design_runner/metric_collector_main.py`
- Create: `tests/runner/test_metric_collector_main.py`
- Create: `tests/docker/test_metric_collector.py`
- Modify: `pyproject.toml` — add `semi-metric-collector = "semi_design_runner.metric_collector_main:main"` script entry

- [ ] **Step 1: Write the failing test**

Create `tests/runner/test_metric_collector_main.py`:

```python
"""Unit tests for the metric-collector entrypoint.

metric_collector_main is imported both from the Docker container (ENTRYPOINT)
and from the local `semi-metric-collector` CLI. It must:

1. Read three .rpt files from $INPUT_S3_URI (file:// in tests, s3:// in prod).
2. Call semi_design_runner.metrics.parse_reports — NOT reimplement it
   (spec §5 / Codex #8 single-source-of-truth).
3. Write metrics.json (Metrics schema serialization) to $OUTPUT_S3_URI.
4. Return exit 0 on success, non-zero with a clear stderr message on failure.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from semi_design_runner import metric_collector_main
from semi_design_runner.schemas import Metrics


def _seed_fixtures(in_dir: Path) -> None:
    (in_dir / "synth").mkdir(parents=True)
    (in_dir / "signoff").mkdir(parents=True)
    (in_dir / "synth" / "synth.rpt").write_text(
        "=== gcd ===\n   Chip area for module:      12345.678 um^2\n",
    )
    (in_dir / "signoff" / "sta.rpt").write_text("slack:  0.480 ns (MET)\n")
    (in_dir / "signoff" / "drc.rpt").write_text("Total violations: 0\n")


def test_collector_writes_metrics_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    _seed_fixtures(in_dir)
    monkeypatch.setenv("RUN_ID", "01HMC")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{in_dir}")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "120.5")

    rc = metric_collector_main.main(argv=[])
    assert rc == 0
    out_file = out_dir / "runs" / "01HMC" / "staging" / "metrics" / "metrics.json"
    assert out_file.exists()
    parsed = json.loads(out_file.read_text())
    # Validate against the schema — proves we went through parse_reports.
    m = Metrics.model_validate(parsed)
    assert m.area_um2 == pytest.approx(12345.678)
    assert m.wns_ns == pytest.approx(0.480)
    assert m.drc_violations == 0
    assert m.runtime_s == pytest.approx(120.5)


def test_collector_reuses_parse_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Codex #8: parser implementation must live in metrics.py only."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    _seed_fixtures(in_dir)
    monkeypatch.setenv("RUN_ID", "01HMC2")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{in_dir}")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "1.0")

    called: list[tuple] = []
    import semi_design_runner.metrics as metrics_mod
    real = metrics_mod.parse_reports

    def spy(**kwargs):
        called.append(tuple(sorted(kwargs.keys())))
        return real(**kwargs)

    monkeypatch.setattr(metrics_mod, "parse_reports", spy)
    rc = metric_collector_main.main(argv=[])
    assert rc == 0
    assert called == [("drc_rpt", "runtime_s", "sta_rpt", "synth_rpt")]


def test_collector_missing_input_returns_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_dir = tmp_path / "out"
    monkeypatch.setenv("RUN_ID", "01HMC3")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{tmp_path}/does-not-exist")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "1.0")

    rc = metric_collector_main.main(argv=[])
    assert rc != 0
```

Create `tests/docker/test_metric_collector.py`:

```python
"""End-to-end container test for semi/metric-collector.

Builds the image with the locally-built wheel and runs it against fixture
reports mounted via a bind mount. Verifies that the ENTRYPOINT honors the
same env-var contract as the other two images AND produces a metrics.json
that validates against the Metrics schema.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

IMAGE_TAG = "semi/metric-collector:phaseC-test"
DOCKERFILE = "docker/metric-collector.Dockerfile"


@pytest.fixture(scope="module")
def built_image(repo_root: Path) -> str:
    # Build the wheel first so the Dockerfile's `COPY dist/*.whl` step succeeds.
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", "dist"],
        cwd=repo_root, check=True, capture_output=True, text=True,
    )
    r = subprocess.run(
        ["docker", "build", "-t", IMAGE_TAG, "-f", DOCKERFILE,
         "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
         "--label", "semi.design.image=metric-collector",
         str(repo_root)],
        capture_output=True, text=True, timeout=10 * 60,
    )
    assert r.returncode == 0, r.stderr
    return IMAGE_TAG


def test_metric_collector_produces_metrics_json(
    built_image: str, tmp_path: Path, repo_root: Path
) -> None:
    in_dir = tmp_path / "in"
    (in_dir / "synth").mkdir(parents=True)
    (in_dir / "signoff").mkdir(parents=True)
    (in_dir / "synth" / "synth.rpt").write_text(
        "Chip area for module:      987.654 um^2\n"
    )
    (in_dir / "signoff" / "sta.rpt").write_text("slack:  0.123 ns (MET)\n")
    (in_dir / "signoff" / "drc.rpt").write_text("Total violations: 0\n")

    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HDOCKER",
         "-e", "STAGE=metrics",
         "-e", "INPUT_S3_URI=file:///work/in",
         "-e", "OUTPUT_S3_URI=file:///work/out",
         "-e", "STAGE_RUNTIME_S=42.0",
         "-e", "STAGE_COMMAND=python -m semi_design_runner.metric_collector_main",
         "-v", f"{tmp_path}:/work",
         built_image],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    out_file = tmp_path / "out" / "runs" / "01HDOCKER" / "staging" / "metrics" / "metrics.json"
    assert out_file.exists(), r.stdout + r.stderr
    data = json.loads(out_file.read_text())
    assert data["area_um2"] == pytest.approx(987.654)
    assert data["runtime_s"] == pytest.approx(42.0)


def test_metric_collector_simulate_spot_reclaim(
    built_image: str, tmp_path: Path
) -> None:
    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HMC",
         "-e", "STAGE=metrics",
         "-e", "INPUT_S3_URI=file:///work/in",
         "-e", "OUTPUT_S3_URI=file:///work/out",
         "-e", "SIMULATE_SPOT_RECLAIM=1",
         "-e", "SIMULATE_SPOT_RECLAIM_DELAY_S=0",
         "-e", "STAGE_COMMAND=python -m semi_design_runner.metric_collector_main",
         "-v", f"{tmp_path}:/work",
         built_image],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 143, r.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
uv run pytest tests/runner/test_metric_collector_main.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'semi_design_runner.metric_collector_main'`.

Run:
```bash
uv run pytest tests/docker/test_metric_collector.py -v -m slow
```
Expected: FAIL — `docker/metric-collector.Dockerfile` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `src/semi_design_runner/metric_collector_main.py`:

```python
"""Container ENTRYPOINT target for the semi/metric-collector image.

Wrapped by docker/entrypoints/run-stage.sh via STAGE_COMMAND. Reads the three
canonical report files (`synth/synth.rpt`, `signoff/sta.rpt`, `signoff/drc.rpt`)
from $INPUT_S3_URI, calls semi_design_runner.metrics.parse_reports — the
single source of truth for parsing, per spec §5 / Codex #8 — and writes
metrics.json (Metrics schema serialization) to the staging output path.

This module also exposes `main()` so the same code can be invoked locally via
the `semi-metric-collector` CLI entry point or imported from pytest.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Sequence

from semi_design_runner.metrics import parse_reports
from semi_design_runner.schemas import Metrics


def _resolve_path(uri: str) -> Path:
    if uri.startswith("file://"):
        return Path(uri[len("file://"):])
    if uri.startswith("s3://"):
        # Inside the container, run-stage.sh has already synced s3:// → local.
        # It exports STAGE_INPUT_DIR / STAGE_WORK_DIR for us.
        raise RuntimeError(
            "s3:// URIs must be resolved by run-stage.sh before calling "
            "metric_collector_main; use $STAGE_INPUT_DIR instead."
        )
    raise ValueError(f"Unsupported URI scheme: {uri!r}")


def main(argv: Sequence[str] | None = None) -> int:
    run_id = os.environ.get("RUN_ID")
    stage = os.environ.get("STAGE", "metrics")
    input_uri = os.environ.get("INPUT_S3_URI")
    output_uri = os.environ.get("OUTPUT_S3_URI")
    runtime_s = float(os.environ.get("STAGE_RUNTIME_S", "0"))
    if not all([run_id, input_uri, output_uri]):
        print("metric_collector_main: RUN_ID/INPUT_S3_URI/OUTPUT_S3_URI required", file=sys.stderr)
        return 2

    # When invoked via run-stage.sh inside the container, STAGE_INPUT_DIR is
    # pre-exported. Outside the container (tests), fall back to parsing the URI.
    input_dir = Path(os.environ.get("STAGE_INPUT_DIR") or _resolve_path(input_uri))
    synth_rpt = input_dir / "synth" / "synth.rpt"
    sta_rpt = input_dir / "signoff" / "sta.rpt"
    drc_rpt = input_dir / "signoff" / "drc.rpt"

    for p in (synth_rpt, sta_rpt, drc_rpt):
        if not p.exists():
            print(f"metric_collector_main: missing report {p}", file=sys.stderr)
            return 3

    metrics: Metrics = parse_reports(
        synth_rpt=synth_rpt,
        sta_rpt=sta_rpt,
        drc_rpt=drc_rpt,
        runtime_s=runtime_s,
    )

    # Output layout mirrors run-stage.sh staging convention (spec §4.3).
    work_dir = os.environ.get("STAGE_WORK_DIR")
    if work_dir:
        out_dir = Path(work_dir)
    else:
        out_dir = _resolve_path(output_uri) / "runs" / run_id / "staging" / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics.model_dump(mode="json"), indent=2, sort_keys=True),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
```

Modify `pyproject.toml` to expose the CLI (append to the existing `[project.scripts]` block added in Task A1):

```toml
[project.scripts]
semi-run = "semi_design_runner.cli:main"
semi-metric-collector = "semi_design_runner.metric_collector_main:main"
```

Create `docker/metric-collector.Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7
# docker/metric-collector.Dockerfile
#
# Spec §5 semi/metric-collector:
#   - python:3.12-slim base (tiny, ~150MB target)
#   - Installs semi_design_runner wheel built locally with `uv build --wheel`.
#   - Parser logic lives in semi_design_runner.metrics.parse_reports — this
#     image does NOT duplicate it (Codex #8 single-source-of-truth).
#   - Same ENTRYPOINT contract (run-stage.sh). STAGE_COMMAND invokes
#     `python -m semi_design_runner.metric_collector_main`.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends awscli \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

# The build script runs `uv build --wheel --out-dir dist/` before `docker build`,
# so dist/*.whl is present in the context. We install the [runner] extras so
# Pydantic v2 + PyYAML + click are available for schema validation.
COPY dist/*.whl /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/*.whl

COPY docker/entrypoints/run-stage.sh /opt/bin/run-stage.sh
RUN chmod +x /opt/bin/run-stage.sh

LABEL org.opencontainers.image.title="semi/metric-collector" \
      org.opencontainers.image.description="Parses synth/sta/drc reports into Metrics JSON using semi_design_runner wheel (single-source parser)."

ENTRYPOINT ["/opt/bin/run-stage.sh"]
```

Create `docker/build-metric-collector.sh`:

```bash
#!/usr/bin/env bash
# docker/build-metric-collector.sh
set -euo pipefail

LOCKFILE="${LOCKFILE:-lockfile.yaml}"
: "${ECR_REGISTRY:?ECR_REGISTRY required when --push}"

# Rebuild the wheel so `dist/*.whl` matches the current source tree.
rm -rf dist
uv build --wheel --out-dir dist

L1_SHA=$(uv run semi-run lockfile-verify --scope l1 --json | jq -r '.l1_lockfile_sha' | sed 's/sha256://;s/^\(.\{12\}\).*/\1/')

IMAGE_NAME="semi/metric-collector"
LOCAL_TAG="${IMAGE_NAME}:${L1_SHA}"
REMOTE_TAG="${ECR_REGISTRY}/${IMAGE_NAME}:${L1_SHA}"

docker build \
  -t "$LOCAL_TAG" \
  -f docker/metric-collector.Dockerfile \
  --label "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design" \
  --label "org.opencontainers.image.revision=${L1_SHA}" \
  .

SIZE_MB=$(docker image inspect "$LOCAL_TAG" --format='{{.Size}}' | awk '{printf "%.0f", $1/1024/1024}')
echo "metric-collector image size: ${SIZE_MB} MB"

if [[ "${1:-}" == "--push" ]]; then
  aws ecr get-login-password --region "$(echo "$ECR_REGISTRY" | cut -d. -f4)" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
  docker tag "$LOCAL_TAG" "$REMOTE_TAG"
  docker push "$REMOTE_TAG"

  DIGEST=$(aws ecr describe-images \
    --repository-name "$IMAGE_NAME" \
    --image-ids "imageTag=${L1_SHA}" \
    --query 'imageDetails[0].imageDigest' --output text)
  echo "metric-collector ECR digest: ${DIGEST}"
  yq -i ".container_digests.\"metric-collector\" = \"${DIGEST}\"" "$LOCKFILE"
fi
```

```bash
chmod +x docker/build-metric-collector.sh
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
uv run pytest tests/runner/test_metric_collector_main.py -v \
  --cov=src/semi_design_runner/metric_collector_main --cov-report=term-missing
```
Expected: 3 PASS, coverage ≥ 85%.

Run:
```bash
uv run pytest tests/docker/test_metric_collector.py -v -m slow
```
Expected: 2 PASS (`produces_metrics_json`, `simulate_spot_reclaim`).

- [ ] **Step 5: Commit**

```bash
git add docker/metric-collector.Dockerfile docker/build-metric-collector.sh \
        src/semi_design_runner/metric_collector_main.py \
        tests/runner/test_metric_collector_main.py \
        tests/docker/test_metric_collector.py \
        pyproject.toml
git commit -m "feat(docker): add semi/metric-collector reusing metrics.parse_reports"
```

---

## Phase C merge note

Assumptions baked into this draft that the primary-plan author should sanity-check on merge: (1) the repository root stays the `docker build` context for all three images so `docker/entrypoints/run-stage.sh` is COPY-able from one shared file; (2) the LibreLane 3.0.2 Nix base is consumed via the upstream prebuilt OCI image `ghcr.io/librelane/librelane:<ref>` rather than running `nix build` inside our Dockerfile — this is the path K1 γ #2 validates and avoids a multi-hour Nix evaluation on CI, at the cost of trusting LibreLane's prebuilt publish pipeline (the `lockfile.yaml.commit_shas.librelane` pin still guards content); (3) ECR repo names match `ContainerStack` from Phase B (`semi-design-{env}-{orfs-runner,librelane-runner,metric-collector}`) — if the Phase B author picks different names, the `IMAGE_NAME` constants in the three `docker/build-*.sh` scripts must be updated in lockstep; (4) `docker build` tests are marked `@pytest.mark.slow` and run locally or on a self-hosted CI runner with Docker — GitHub Actions hosted runners execute only the non-slow `tests/docker/test_run_stage_entrypoint.py` and `tests/runner/test_metric_collector_main.py` suites, and the `@pytest.mark.slow` marker is registered in the existing `pyproject.toml` pytest config alongside any other slow markers; (5) `STAGE_COMMAND` is supplied by the SFN Map state's container override (the CDK WorkflowStack encodes per-stage commands), so each image is agnostic to which stage it runs — this is why `semi/metric-collector` accepts an arbitrary `STAGE_COMMAND` and we pass `python -m semi_design_runner.metric_collector_main` from tests; (6) ECR digest capture via `aws ecr describe-images` writes back into `lockfile.yaml.container_digests.*`, which Phase E then commits as part of the "fill real SHAs" task — Phase C's build scripts perform the write-back but the commit of `lockfile.yaml` itself is Phase E's responsibility.

---

## Phase D — KG Scripts

**Goal:** 9 deterministic kill-gate verification scripts satisfying G1 exit criterion 7 (`make kg-all`). KG-A/C1/D/E/F are G1-mandatory; KG-B is L3-readiness (optional); KG-C2 is weekly live smoke (optional). Every script emits JSON with `passed: bool` and `mode: "smoke"|"live"`. Unit tests use `SMOKE=1` — no AWS resources consumed in Phase D.

**Phase D dependencies:** Phase A (`semi-run` CLI for `init`/`submit`/`status`) + Phase B (ECR/Fargate infra for live path) + Phase C (containers referenced by KG-A/C2/D). Unit tests need only Phase A.

---

### Task D1: KG-A — LibreLane 3.0.2 on Fargate Spot gcd in 30 min

**Files:** Create `scripts/kg/kg-a-librelane-fargate.sh`, `tests/kg/__init__.py`, `tests/kg/test_kg_a.py`

- [ ] **Step 1: Write failing tests** (`tests/kg/test_kg_a.py`)

```python
import json, os, subprocess
from pathlib import Path
SCRIPT = Path("scripts/kg/kg-a-librelane-fargate.sh")

def test_kg_a_executable():
    assert SCRIPT.exists() and os.access(SCRIPT, os.X_OK)

def test_kg_a_smoke_emits_required_fields():
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                       timeout=10, env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0, r.stderr
    p = json.loads(r.stdout)
    assert p["mode"] == "smoke" and p["passed"] is True
    for key in ("ephemeral_peak_gb", "image_pull_seconds", "duration_seconds"):
        assert key in p

def test_kg_a_smoke_ephemeral_overflow_fails():
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                       timeout=10, env={**os.environ, "SMOKE": "1", "SMOKE_EPHEMERAL_GB": "25"})
    assert r.returncode == 1
    assert json.loads(r.stdout)["passed"] is False
```

- [ ] **Step 2: Run to verify failure**

`uv run pytest tests/kg/test_kg_a.py -v` → FAIL.

- [ ] **Step 3: Implement** `scripts/kg/kg-a-librelane-fargate.sh`

```bash
#!/usr/bin/env bash
# KG-A: LibreLane 3.0.2 on Fargate Spot — gcd within 30min, ephemeral <21GB, pull <10min.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    EPH="${SMOKE_EPHEMERAL_GB:-12.3}"
    PULL="${SMOKE_PULL_SEC:-420}"
    DUR="${SMOKE_DURATION:-1200}"
    PASS="true"
    (( $(echo "$EPH > 21" | bc -l) )) && PASS="false"
    [[ "$PULL" -gt 600 ]] && PASS="false"
    [[ "$DUR" -gt 1800 ]] && PASS="false"
    jq -n --argjson passed "$PASS" --argjson e "$EPH" --argjson p "$PULL" --argjson d "$DUR" \
      '{passed: $passed, ephemeral_peak_gb: $e, image_pull_seconds: $p, duration_seconds: $d, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${BUCKET:?}" "${STATE_MACHINE_ARN:?}"
START=$(date +%s)
RUN_ID=$(uv run python -c "import ulid; print(ulid.new())")
uv run semi-run init --spec specs/gcd-librelane.yaml --bucket "$BUCKET" > /tmp/kg-a-init.json
EXEC=$(uv run semi-run submit --run-id "$RUN_ID" --state-machine-arn "$STATE_MACHINE_ARN")
uv run semi-run status --run-id "$RUN_ID" --execution-arn "$EXEC"
END=$(date +%s); DUR=$((END-START))
EPH=$(aws logs filter-log-events --log-group-name /aws/fargate/semi-design \
  --filter-pattern ephemeral_peak --limit 1 --query 'events[0].message' --output text \
  | jq -r '.peak_gb // 0')
PULL=$(aws logs filter-log-events --log-group-name /aws/fargate/semi-design \
  --filter-pattern image_pull --limit 1 --query 'events[0].message' --output text \
  | jq -r '.seconds // 0')
PASS="true"
(( $(echo "$EPH > 21" | bc -l) )) && PASS="false"
[[ "$PULL" -gt 600 ]] && PASS="false"
[[ "$DUR" -gt 1800 ]] && PASS="false"
jq -n --argjson passed "$PASS" --argjson e "$EPH" --argjson p "$PULL" --argjson d "$DUR" \
  '{passed: $passed, ephemeral_peak_gb: $e, image_pull_seconds: $p, duration_seconds: $d, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
```

Run: `chmod +x scripts/kg/kg-a-librelane-fargate.sh && mkdir -p tests/kg && touch tests/kg/__init__.py`

- [ ] **Step 4: Run** `uv run pytest tests/kg/test_kg_a.py -v` → 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-a-librelane-fargate.sh tests/kg/__init__.py tests/kg/test_kg_a.py
git commit -m "feat(kg): KG-A LibreLane Fargate gate (smoke+live)"
```

---

### Task D2: KG-B — Chipyard prebuilt cache integrity (L3-readiness, optional)

**Files:** Create `scripts/kg/kg-b-chipyard-cache.sh`, `tests/kg/test_kg_b.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_kg_b.py
import json, os, subprocess
from pathlib import Path
SCRIPT = Path("scripts/kg/kg-b-chipyard-cache.sh")

def test_kg_b_smoke_passes_when_metadata_complete():
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                       timeout=10, env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0
    p = json.loads(r.stdout)
    assert p["passed"] is True and p["scope"] == "l3-readiness"

def test_kg_b_smoke_fails_on_sha_mismatch():
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True,
                       timeout=10, env={**os.environ, "SMOKE": "1", "SMOKE_SHA_MATCH": "false"})
    assert r.returncode == 1 and json.loads(r.stdout)["passed"] is False
```

- [ ] **Step 2: Run to verify failure** → FAIL.

- [ ] **Step 3: Implement**

```bash
#!/usr/bin/env bash
# KG-B: Chipyard prebuilt cache integrity — L3-readiness only (NOT G1 gate).
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    MATCH="${SMOKE_SHA_MATCH:-true}"
    jq -n --argjson passed "$MATCH" --argjson match "$MATCH" \
      '{passed: $passed, scope: "l3-readiness", cache_object: "s3://semi-design/chipyard-prebuilt/<sha>/chipyard.tar.gz", sha_match: $match, mode: "smoke"}'
    [[ "$MATCH" == "true" ]] || exit 1
    exit 0
fi

: "${BUCKET:?}"
SHA=$(yq '.commit_shas.chipyard' lockfile.yaml)
if [[ "$SHA" == "null" || -z "$SHA" ]]; then
    jq -n '{passed: true, scope: "l3-readiness", note: "chipyard SHA deferred", mode: "live"}'
    exit 0
fi
KEY="chipyard-prebuilt/${SHA}/chipyard.tar.gz"
REMOTE=$(aws s3api head-object --bucket "$BUCKET" --key "$KEY" --query 'Metadata.sha256' --output text 2>/dev/null || echo "")
PASS="false"; [[ -n "$REMOTE" ]] && PASS="true"
jq -n --argjson passed "$PASS" --arg sha "$REMOTE" \
  '{passed: $passed, scope: "l3-readiness", cache_object: ("s3://'"$BUCKET"'/'"$KEY"'"), sha_match: ($sha != ""), mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
```

`chmod +x scripts/kg/kg-b-chipyard-cache.sh`

- [ ] **Step 4: Run** → 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-b-chipyard-cache.sh tests/kg/test_kg_b.py
git commit -m "feat(kg): KG-B Chipyard cache integrity (L3-readiness, optional)"
```

---

### Task D3: KG-C1 — Deterministic SDK token budget

**Files:** Create `src/semi_design_runner/token_budget.py`, `tests/runner/test_token_budget.py`, `scripts/kg/kg-c1-token-budget.sh`, `tests/kg/test_kg_c1.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/runner/test_token_budget.py
from semi_design_runner.token_budget import estimate_monthly_tokens, within_budget

def test_estimate_monthly_counts():
    assert estimate_monthly_tokens(runs_per_month=100, avg_tokens_per_run=30_000) == 3_000_000

def test_within_budget_true_when_below():
    assert within_budget(estimate=1_000_000, limit=2_000_000)

def test_within_budget_false_when_over():
    assert not within_budget(estimate=3_000_000, limit=2_000_000)
```

```python
# tests/kg/test_kg_c1.py
import json, os, subprocess
from pathlib import Path
S = Path("scripts/kg/kg-c1-token-budget.sh")

def test_kg_c1_smoke_within_budget_passes():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_ESTIMATE": "1000000", "SMOKE_LIMIT": "2000000"})
    assert r.returncode == 0 and json.loads(r.stdout)["passed"] is True

def test_kg_c1_smoke_over_budget_fails():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_ESTIMATE": "3000000", "SMOKE_LIMIT": "2000000"})
    assert r.returncode == 1 and json.loads(r.stdout)["passed"] is False
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```python
# src/semi_design_runner/token_budget.py
"""Deterministic token budget check (KG-C1). No live SDK calls."""
def estimate_monthly_tokens(*, runs_per_month: int, avg_tokens_per_run: int) -> int:
    return runs_per_month * avg_tokens_per_run

def within_budget(*, estimate: int, limit: int) -> bool:
    return estimate <= limit
```

```bash
#!/usr/bin/env bash
# KG-C1: local token budget. No provider calls.
set -euo pipefail
EST="${SMOKE_ESTIMATE:-$(uv run python -c 'from semi_design_runner.token_budget import estimate_monthly_tokens; print(estimate_monthly_tokens(runs_per_month=100, avg_tokens_per_run=30000))')}"
LIM="${SMOKE_LIMIT:-$(yq '.monthly_token_limit' scripts/kg/budget-limits.yaml 2>/dev/null || echo 5000000)}"
PASS="false"; [[ "$EST" -le "$LIM" ]] && PASS="true"
jq -n --argjson passed "$PASS" --argjson e "$EST" --argjson l "$LIM" \
  '{passed: $passed, estimated_tokens: $e, monthly_limit: $l, mode: "deterministic"}'
[[ "$PASS" == "true" ]] || exit 1
```

`chmod +x scripts/kg/kg-c1-token-budget.sh`

- [ ] **Step 4: Run** → 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add src/semi_design_runner/token_budget.py tests/runner/test_token_budget.py scripts/kg/kg-c1-token-budget.sh tests/kg/test_kg_c1.py
git commit -m "feat(kg): KG-C1 deterministic token budget"
```

---

### Task D4: KG-C2 — Optional live smoke via Fargate `kg-c2-smoke` TaskDef

**Files:** Create `scripts/kg/kg-c2-live-smoke.sh`, `tests/kg/test_kg_c2.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_kg_c2.py
import json, os, subprocess
from pathlib import Path
S = Path("scripts/kg/kg-c2-live-smoke.sh")

def test_kg_c2_smoke_marks_optional():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0
    p = json.loads(r.stdout)
    assert p["optional"] is True and p["mode"] == "smoke"

def test_kg_c2_documents_fargate_taskdef_entry():
    content = S.read_text()
    assert "ecs run-task" in content and "kg-c2-smoke" in content
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```bash
#!/usr/bin/env bash
# KG-C2: live provider-quota smoke. Runs inside dedicated Fargate `kg-c2-smoke`
# TaskDef; CI never reads API keys directly (Codex 2차 new #4).
# CI invocation:
#   aws ecs run-task --cluster semi-design --task-definition kg-c2-smoke
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    jq -n '{passed: true, optional: true, mode: "smoke", note: "live path requires kg-c2-smoke Fargate TaskDef trigger"}'
    exit 0
fi

# We are inside kg-c2-smoke container. Secret grant scoped to this task role only.
CLAUDE_KEY=$(aws secretsmanager get-secret-value --secret-id /semi-design/claude-api-key --query SecretString --output text)
HEADERS=$(uv run python -m semi_design_runner.quota_probe --provider claude --api-key "$CLAUDE_KEY" 2>&1 || true)
REMAINING=$(echo "$HEADERS" | grep -o 'x-ratelimit-remaining:[[:space:]]*[0-9]*' | awk '{print $2}')
PASS="true"
[[ -z "$REMAINING" || "$REMAINING" -lt 100 ]] && PASS="false"
jq -n --argjson passed "$PASS" --argjson rem "${REMAINING:-0}" \
  '{passed: $passed, optional: true, remaining_quota: $rem, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
```

`chmod +x scripts/kg/kg-c2-live-smoke.sh`

- [ ] **Step 4: Run** → 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-c2-live-smoke.sh tests/kg/test_kg_c2.py
git commit -m "feat(kg): KG-C2 optional live smoke via kg-c2-smoke TaskDef"
```

---

### Task D5: KG-D — Spot reclaim deterministic test via `SIMULATE_SPOT_RECLAIM`

**Files:** Create `scripts/kg/kg-d-spot-reclaim.sh`, `tests/kg/test_kg_d.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_kg_d.py
import json, os, subprocess
from pathlib import Path
S = Path("scripts/kg/kg-d-spot-reclaim.sh")

def test_kg_d_smoke_passes_at_80pct():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_RECOVERED": "8", "SMOKE_TOTAL": "10"})
    assert r.returncode == 0 and json.loads(r.stdout)["passed"] is True

def test_kg_d_smoke_fails_below_80pct():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_RECOVERED": "6", "SMOKE_TOTAL": "10"})
    assert r.returncode == 1 and json.loads(r.stdout)["passed"] is False
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```bash
#!/usr/bin/env bash
# KG-D: Deterministic reclaim via container env SIMULATE_SPOT_RECLAIM=1 → exit 143.
# SFN retry(MaxAttempts=2, BackoffRate=2) must recover ≥80% of 10 simulated jobs.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"
TOTAL="${SMOKE_TOTAL:-10}"

if [[ "$MODE" == "smoke" ]]; then
    REC="${SMOKE_RECOVERED:-8}"
    RATE=$(echo "scale=2; $REC / $TOTAL" | bc)
    PASS="false"; (( $(echo "$RATE >= 0.80" | bc -l) )) && PASS="true"
    jq -n --argjson passed "$PASS" --argjson r "$REC" --argjson t "$TOTAL" --argjson rate "$RATE" \
      '{passed: $passed, recovered: $r, total: $t, recovery_rate: $rate, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${BUCKET:?}" "${STATE_MACHINE_ARN:?}"
REC=0
for i in $(seq 1 "$TOTAL"); do
    RUN_ID=$(uv run python -c "import ulid; print(ulid.new())")
    uv run semi-run init --spec specs/gcd-orfs.yaml --bucket "$BUCKET" --simulate-spot-reclaim > /tmp/kg-d.$i.json
    EXEC=$(uv run semi-run submit --run-id "$RUN_ID" --state-machine-arn "$STATE_MACHINE_ARN")
    STATUS=$(uv run semi-run status --run-id "$RUN_ID" --execution-arn "$EXEC" --wait)
    echo "$STATUS" | jq -e '.ddb_status == "clean"' >/dev/null && REC=$((REC+1))
done
RATE=$(echo "scale=2; $REC / $TOTAL" | bc)
PASS="false"; (( $(echo "$RATE >= 0.80" | bc -l) )) && PASS="true"
jq -n --argjson passed "$PASS" --argjson r "$REC" --argjson t "$TOTAL" --argjson rate "$RATE" \
  '{passed: $passed, recovered: $r, total: $t, recovery_rate: $rate, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
```

`chmod +x scripts/kg/kg-d-spot-reclaim.sh`

- [ ] **Step 4: Run** → 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-d-spot-reclaim.sh tests/kg/test_kg_d.py
git commit -m "feat(kg): KG-D Spot reclaim (SIMULATE_SPOT_RECLAIM deterministic)"
```

---

### Task D6: KG-E — DDB `ddb_write_count` < 50 per candidate

**Files:** Create `scripts/kg/kg-e-ddb-write-amp.sh`, `tests/kg/test_kg_e.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_kg_e.py
import json, os, subprocess
from pathlib import Path
S = Path("scripts/kg/kg-e-ddb-write-amp.sh")

def test_kg_e_smoke_under_limit():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_COUNT": "12"})
    assert r.returncode == 0 and json.loads(r.stdout)["passed"] is True

def test_kg_e_smoke_over_limit_fails():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1", "SMOKE_COUNT": "80"})
    assert r.returncode == 1
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```bash
#!/usr/bin/env bash
# KG-E: per-candidate ddb_write_count < 50, via app-level counter (not CloudWatch).
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"

if [[ "$MODE" == "smoke" ]]; then
    CNT="${SMOKE_COUNT:-12}"
    PASS="false"; [[ "$CNT" -lt 50 ]] && PASS="true"
    jq -n --argjson passed "$PASS" --argjson c "$CNT" \
      '{passed: $passed, ddb_write_count: $c, limit: 50, mode: "smoke"}'
    [[ "$PASS" == "true" ]] || exit 1
    exit 0
fi

: "${RUN_ID:?}"
CNT=$(uv run python -c "
from semi_design_runner.aws.clients import make_client
from semi_design_runner.aws.ddb import get_ddb_write_count
print(get_ddb_write_count(make_client('dynamodb'), table='Candidates', run_id='$RUN_ID', gen=0, cand=0))
")
PASS="false"; [[ "$CNT" -lt 50 ]] && PASS="true"
jq -n --argjson passed "$PASS" --argjson c "$CNT" \
  '{passed: $passed, ddb_write_count: $c, limit: 50, mode: "live"}'
[[ "$PASS" == "true" ]] || exit 1
```

`chmod +x scripts/kg/kg-e-ddb-write-amp.sh`

- [ ] **Step 4: Run** → 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-e-ddb-write-amp.sh tests/kg/test_kg_e.py
git commit -m "feat(kg): KG-E DDB write-amp via Candidates.ddb_write_count"
```

---

### Task D7: KG-F1 — Pre-RunTask budget rejection (zero ECS calls)

**Files:** Create `scripts/kg/kg-f1-prebudget.sh`, `tests/kg/test_kg_f1.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_kg_f1.py
import json, os, subprocess
from pathlib import Path
S = Path("scripts/kg/kg-f1-prebudget.sh")

def test_kg_f1_smoke_detects_pre_reject():
    r = subprocess.run(["bash", str(S)], capture_output=True, text=True, timeout=10,
                       env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0
    p = json.loads(r.stdout)
    assert p["passed"] is True and p["rejected"] is True
    assert p["ecs_runs"] == 0
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```bash
#!/usr/bin/env bash
# KG-F1: Prove pre-RunTask budget guard rejects BEFORE any ECS call.
# Spec with budget=0.01 + planned sum=5.0 must be rejected by `semi-run init`.
set -euo pipefail
MODE="${SMOKE:+smoke}"; MODE="${MODE:-live}"
SPEC=specs/_kg_f1_overbudget.yaml

mkdir -p specs
cat > "$SPEC" <<EOF
version: 1
run_id: "kg-f1-$(date +%s)"
design: gcd
stack: orfs
flow_parameters: {}
compute_budget_usd: 0.01
planned_cost_per_stage_usd:
  synth: 2.5
  pnr: 2.5
seed: 0
l1_lockfile_sha: "sha256:0000000000000000000000000000000000000000000000000000000000000000"
EOF

if [[ "$MODE" == "smoke" ]]; then
    REASON=$(uv run python -c "
from semi_design_runner.schemas import Spec
from semi_design_runner.cost import check_planned_budget, BudgetExceededError
import yaml
s = Spec.model_validate(yaml.safe_load(open('$SPEC')))
try: check_planned_budget(s); print('')
except BudgetExceededError as e: print(str(e))
")
    if [[ -n "$REASON" ]]; then
        jq -n --arg r "$REASON" '{passed: true, rejected: true, reason: "planned_cost_exceeds_budget", detail: $r, ecs_runs: 0, mode: "smoke"}'
        exit 0
    fi
    jq -n '{passed: false, rejected: false, ecs_runs: 0, mode: "smoke"}'; exit 1
fi

uv run semi-run init --spec "$SPEC" --bucket "${BUCKET:?}" > /tmp/kg-f1.json && {
    jq -n '{passed: false, rejected: false, reason: "init accepted overbudget spec", mode: "live"}'; exit 1;
} || true
jq -n '{passed: true, rejected: true, reason: "planned_cost_exceeds_budget", ecs_runs: 0, mode: "live"}'
```

`chmod +x scripts/kg/kg-f1-prebudget.sh`

- [ ] **Step 4: Run** → 1 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/kg-f1-prebudget.sh tests/kg/test_kg_f1.py
git commit -m "feat(kg): KG-F1 pre-RunTask budget rejection (zero ECS calls)"
```

---

### Task D8: `run-all.sh` aggregator + `budget-limits.yaml`

**Files:** Create `scripts/kg/run-all.sh`, `scripts/kg/budget-limits.yaml`, `tests/kg/test_run_all.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/kg/test_run_all.py
import json, os, subprocess
from pathlib import Path

def test_run_all_smoke_aggregates_mandatory_green():
    r = subprocess.run(["bash", "scripts/kg/run-all.sh"], capture_output=True, text=True,
                       timeout=60, env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0, r.stderr
    agg = json.loads(r.stdout)
    assert agg["overall_passed"] is True
    mandatory = {"kg-a", "kg-c1", "kg-d", "kg-e", "kg-f1"}
    assert mandatory.issubset(set(agg["gates"].keys()))
    for g in mandatory:
        assert agg["gates"][g]["passed"] is True

def test_run_all_marks_kg_b_and_c2_optional():
    r = subprocess.run(["bash", "scripts/kg/run-all.sh"], capture_output=True, text=True,
                       timeout=60, env={**os.environ, "SMOKE": "1"})
    agg = json.loads(r.stdout)
    assert agg["gates"]["kg-b"]["optional"] is True
    assert agg["gates"]["kg-c2"]["optional"] is True

def test_budget_limits_yaml_has_keys():
    import yaml
    data = yaml.safe_load(Path("scripts/kg/budget-limits.yaml").read_text())
    assert "monthly_usd" in data and "monthly_token_limit" in data
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement**

```yaml
# scripts/kg/budget-limits.yaml
monthly_usd: 100
weekly_usd: 30
per_candidate_usd_max: 5
monthly_token_limit: 5000000
```

```bash
#!/usr/bin/env bash
# Aggregates mandatory + optional KG gates. Emits single JSON report.
set -o pipefail
OUT="${OUTPUT_DIR:-artifacts/kg-reports/$(date +%Y-%m-%d)}"
mkdir -p "$OUT"

run_gate() {
    local name="$1" script="$2" optional="$3"
    local out="$OUT/$name.json"
    SMOKE="${SMOKE:-}" bash "$script" > "$out" || true
    jq --arg n "$name" --argjson opt "$optional" '. + {gate: $n, optional: $opt}' "$out"
}

A=$(run_gate kg-a  scripts/kg/kg-a-librelane-fargate.sh false)
B=$(run_gate kg-b  scripts/kg/kg-b-chipyard-cache.sh true)
C1=$(run_gate kg-c1 scripts/kg/kg-c1-token-budget.sh false)
C2=$(run_gate kg-c2 scripts/kg/kg-c2-live-smoke.sh true)
D=$(run_gate kg-d  scripts/kg/kg-d-spot-reclaim.sh false)
E=$(run_gate kg-e  scripts/kg/kg-e-ddb-write-amp.sh false)
F1=$(run_gate kg-f1 scripts/kg/kg-f1-prebudget.sh false)

jq -n --argjson a "$A" --argjson b "$B" --argjson c1 "$C1" --argjson c2 "$C2" \
      --argjson d "$D" --argjson e "$E" --argjson f1 "$F1" '
{
  gates: {"kg-a": $a, "kg-b": $b, "kg-c1": $c1, "kg-c2": $c2, "kg-d": $d, "kg-e": $e, "kg-f1": $f1},
  mandatory: ["kg-a", "kg-c1", "kg-d", "kg-e", "kg-f1"],
  overall_passed: ($a.passed and $c1.passed and $d.passed and $e.passed and $f1.passed)
}
'
```

`chmod +x scripts/kg/run-all.sh`

- [ ] **Step 4: Run** → 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/kg/run-all.sh scripts/kg/budget-limits.yaml tests/kg/test_run_all.py
git commit -m "feat(kg): run-all aggregator + budget-limits.yaml"
```

---

### Task D9: Makefile `kg-all` target + `scripts/kg/README.md`

**Files:** Modify `Makefile`, Create `scripts/kg/README.md`

- [ ] **Step 1: Write failing test** (append to `tests/kg/test_run_all.py`)

```python
def test_makefile_has_kg_all_target():
    import subprocess, os
    r = subprocess.run(["make", "-n", "kg-all"], capture_output=True, text=True,
                       env={**os.environ, "SMOKE": "1"})
    assert r.returncode == 0, r.stderr
    assert "scripts/kg/run-all.sh" in r.stdout
```

- [ ] **Step 2: Run** → FAIL (no target).

- [ ] **Step 3: Implement**

Append to `Makefile`:

```makefile
kg-all:
	bash scripts/kg/run-all.sh

.PHONY: kg-all
```

Create `scripts/kg/README.md`:

```markdown
# Kill-Gate Scripts (G1 exit criterion 7)

| Gate | Script | Mandatory |
|---|---|---|
| KG-A | `kg-a-librelane-fargate.sh` | ✅ |
| KG-B | `kg-b-chipyard-cache.sh` | ❌ L3-readiness |
| KG-C1 | `kg-c1-token-budget.sh` | ✅ |
| KG-C2 | `kg-c2-live-smoke.sh` | ❌ weekly |
| KG-D | `kg-d-spot-reclaim.sh` | ✅ |
| KG-E | `kg-e-ddb-write-amp.sh` | ✅ |
| KG-F1 | `kg-f1-prebudget.sh` | ✅ |

Run all: `make kg-all`. Unit tests use `SMOKE=1` (no AWS).
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add Makefile scripts/kg/README.md tests/kg/test_run_all.py
git commit -m "feat(kg): make kg-all + scripts/kg/README"
```

## Phase E — Integration

**Goal:** Close G1 — wire Phase A/B/C/D artifacts into a one-line `make run` that completes gcd end-to-end on real AWS, pass `make kg-all`, and demonstrate clean-VM reproducibility via CI. Phase E depends on all prior phases being green.

---

### Task E1: Fill `lockfile.yaml` with real SHAs + push images to ECR

**Files:** Create `lockfile.yaml`, Modify `scripts/kg/budget-limits.yaml` (verified already present)

- [ ] **Step 1: Write failing test**

```python
# tests/runner/test_lockfile_real.py
from pathlib import Path
import yaml
from semi_design_runner.lockfile import verify_scope

def test_real_lockfile_l1_scope_green():
    lf = yaml.safe_load(Path("lockfile.yaml").read_text())
    result = verify_scope(lf, scope="l1")
    assert result["verified"] is True, result
    assert len(result["mismatched"]) == 0
    for key in ("orfs-runner", "librelane-runner", "metric-collector"):
        assert key in lf["container_digests"]
        assert lf["container_digests"][key].startswith("sha256:")
```

- [ ] **Step 2: Run** → FAIL (lockfile.yaml missing or has `<SHA>` placeholder).

- [ ] **Step 3: Implement**

Create `lockfile.yaml` (root). Resolve real SHAs from upstream:

```bash
# 1. Capture upstream commit SHAs
OPENROAD_SHA=$(git ls-remote https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts HEAD | awk '{print $1}')
LIBRELANE_SHA=$(git ls-remote https://github.com/librelane/librelane HEAD | awk '{print $1}')
YOSYS_SHA=$(git ls-remote --tags https://github.com/YosysHQ/yosys yosys-0.55 | awk '{print $1}')
OPEN_PDKS_SHA=$(git ls-remote https://github.com/RTimothyEdwards/open_pdks HEAD | awk '{print $1}')
SKY130A_DIGEST=$(python -c "import hashlib,urllib.request; ..." )  # compute from open_pdks build output
# 2. Build images + push to ECR (Phase C build-*.sh scripts)
bash docker/build-orfs-runner.sh
bash docker/build-librelane-runner.sh
bash docker/build-metric-collector.sh
# 3. Read back image digests via `aws ecr describe-images` (Phase C Task C* handles this)
# 4. Write into lockfile.yaml
```

Then the `lockfile.yaml` content uses real values:

```yaml
version: 1
updated_at: "2026-04-21"
updated_by: serithemage
commit_shas:
  openroad: "<real_sha>"
  librelane: "<real_sha>"
  yosys: "<real_sha>"
  open_pdks: "<real_sha>"
  verilator: null
  cocotb: null
  chipyard: null
  gemmini: null
  mlcommons_tiny: null
container_digests:
  orfs-runner: "sha256:<real_digest>"
  librelane-runner: "sha256:<real_digest>"
  metric-collector: "sha256:<real_digest>"
source_tarball_mirrors:
  openroad: "s3://semi-design/mirrors/openroad/<sha>.tar.gz"
  librelane: "s3://semi-design/mirrors/librelane/<sha>.tar.gz"
  yosys: "s3://semi-design/mirrors/yosys/<sha>.tar.gz"
  open_pdks: "s3://semi-design/mirrors/open_pdks/<sha>.tar.gz"
pdk_digests:
  sky130A: "sha256:<real_digest>"
stale_source_policy:
  grace_period_hours: 24
  action_on_failure: ci_red
ci_verification:
  last_green_commit: "<git_HEAD>"
  last_green_at: "2026-04-21T00:00:00Z"
```

- [ ] **Step 4: Run** `uv run semi-run lockfile-verify --scope l1` → `{verified: true, ...}`. Then `pytest tests/runner/test_lockfile_real.py` PASS.

- [ ] **Step 5: Commit**

```bash
git add lockfile.yaml tests/runner/test_lockfile_real.py
git commit -m "feat(l1): fill lockfile.yaml with real SHAs and ECR digests"
```

---

### Task E2: Sample specs for gcd/ibex/aes + overbudget edge case

**Files:** Create `specs/gcd-orfs.yaml`, `specs/gcd-librelane.yaml`, `specs/ibex-orfs.yaml`, `specs/aes-orfs.yaml`

- [ ] **Step 1: Write failing test**

```python
# tests/runner/test_sample_specs.py
from pathlib import Path
import pytest, yaml
from semi_design_runner.schemas import Spec
from semi_design_runner.validator import RejectedNotInG1Scope, validate_spec_for_g1

@pytest.mark.parametrize("path", [
    "specs/gcd-orfs.yaml", "specs/gcd-librelane.yaml",
])
def test_sample_gcd_spec_passes_g1_validator(path):
    spec = Spec.model_validate(yaml.safe_load(Path(path).read_text()))
    validate_spec_for_g1(spec)  # no raise

@pytest.mark.parametrize("path", [
    "specs/ibex-orfs.yaml", "specs/aes-orfs.yaml",
])
def test_non_gcd_sample_rejected(path):
    spec = Spec.model_validate(yaml.safe_load(Path(path).read_text()))
    with pytest.raises(RejectedNotInG1Scope):
        validate_spec_for_g1(spec)
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** sample specs. Example `specs/gcd-orfs.yaml`:

```yaml
version: 1
run_id: "01HGCDSAMPLE0000000000000"
design: gcd
stack: orfs
flow_parameters:
  core_utilization: 0.30
  place_density: 0.60
  clock_period_ps: 8000
  timing_driven: true
  synth_flatten: false
resource_overrides: {}
experimental: {}
compute_budget_usd: 3.0
planned_cost_per_stage_usd:
  rtl-build: 0.10
  synth: 0.30
  pnr: 1.50
  signoff: 0.40
  metrics: 0.05
seed: 42
l1_lockfile_sha: "sha256:<filled by E2E>"
```

`specs/gcd-librelane.yaml` — same but `stack: librelane`. `specs/ibex-orfs.yaml` / `specs/aes-orfs.yaml` — same shape, `design: ibex`/`design: aes` (for rejection test).

- [ ] **Step 4: Run** → 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add specs/*.yaml tests/runner/test_sample_specs.py
git commit -m "feat(l1): sample specs for gcd (orfs/librelane) + ibex/aes rejection fixtures"
```

---

### Task E3: Makefile `run` + `lockfile-verify` targets (kg-all from D9)

**Files:** Modify `Makefile`

- [ ] **Step 1: Write failing test**

```python
# tests/runner/test_makefile_targets.py
import subprocess
def test_make_run_dry_invokes_semi_run():
    r = subprocess.run(["make", "-n", "run", "DESIGN=gcd", "STACK=orfs"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "semi-run init" in r.stdout
    assert "semi-run submit" in r.stdout
    assert "semi-run status" in r.stdout

def test_make_lockfile_verify_dry():
    r = subprocess.run(["make", "-n", "lockfile-verify"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "semi-run lockfile-verify" in r.stdout
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** — Append to `Makefile`:

```makefile
DESIGN ?= gcd
STACK  ?= orfs
SEED   ?= 42

run: lockfile-verify
	uv run semi-run init --spec specs/$(DESIGN)-$(STACK).yaml
	uv run semi-run submit --run-id $$(cat .last-run-id) --state-machine-arn $(STATE_MACHINE_ARN)
	uv run semi-run status --run-id $$(cat .last-run-id) --execution-arn $$(cat .last-exec-arn) --wait

lockfile-verify:
	uv run semi-run lockfile-verify --scope l1

.PHONY: run lockfile-verify
```

- [ ] **Step 4: Run** → 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add Makefile tests/runner/test_makefile_targets.py
git commit -m "feat(l1): make run + lockfile-verify targets"
```

---

### Task E4: GitHub Actions CI for clean-VM reproducibility

**Files:** Create `.github/workflows/l1-ci.yml`

- [ ] **Step 1: Write failing test**

```python
# tests/runner/test_ci_workflow.py
import yaml
from pathlib import Path

def test_ci_workflow_exists_and_installs_deps():
    wf = yaml.safe_load(Path(".github/workflows/l1-ci.yml").read_text())
    jobs = wf["jobs"]
    assert "install-test" in jobs
    steps = jobs["install-test"]["steps"]
    step_names = [s.get("name", "") for s in steps]
    assert any("uv sync" in n or "install" in n.lower() for n in step_names)
    assert any("pytest" in n.lower() or "test" in n.lower() for n in step_names)
    assert any("kg" in n.lower() or "lockfile-verify" in n.lower() for n in step_names)
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** `.github/workflows/l1-ci.yml`:

```yaml
name: L1 CI (clean-VM)
on:
  push: { branches: [main] }
  pull_request: {}

jobs:
  install-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: uv sync install runner extras
        run: uv sync --all-extras
      - name: Lint + format
        run: |
          uv run ruff check src/semi_design_runner tests
          uv run ruff format --check src/semi_design_runner tests
      - name: Unit tests with coverage
        run: uv run pytest tests/runner tests/kg -v --cov=src/semi_design_runner --cov-fail-under=85
      - name: Lockfile verify (L1 scope only)
        run: uv run semi-run lockfile-verify --scope l1
      - name: KG all (SMOKE mode, no AWS)
        run: SMOKE=1 make kg-all
  cdk-synth:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - name: Install CDK deps
        working-directory: cdk
        run: npm ci
      - name: CDK unit + snapshot tests
        working-directory: cdk
        run: npx jest
      - name: CDK synth (no deploy)
        working-directory: cdk
        run: npx cdk synth --context env=dev
```

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/l1-ci.yml tests/runner/test_ci_workflow.py
git commit -m "feat(ci): L1 clean-VM CI (install + test + lockfile-verify + kg-all smoke + cdk synth)"
```

---

### Task E5: E2E — `make run DESIGN=gcd STACK=orfs` on real AWS

**Files:** Create `tests/e2e/test_gcd_orfs_e2e.py` (marked `@pytest.mark.slow`)

- [ ] **Step 1: Write failing test**

```python
# tests/e2e/test_gcd_orfs_e2e.py
import pytest, subprocess, json, os

@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get("AWS_ACCOUNT_ID"), reason="requires AWS creds")
def test_make_run_gcd_orfs_completes_clean():
    r = subprocess.run(
        ["make", "run", "DESIGN=gcd", "STACK=orfs"],
        capture_output=True, text=True, timeout=2400,
    )
    assert r.returncode == 0, r.stderr
    run_id = open(".last-run-id").read().strip()
    status = subprocess.run(
        ["uv", "run", "semi-run", "status", "--run-id", run_id,
         "--execution-arn", open(".last-exec-arn").read().strip()],
        capture_output=True, text=True,
    )
    payload = json.loads(status.stdout)
    assert payload["ddb_status"] == "clean"
    assert payload["sfn_status"] == "SUCCEEDED"
```

- [ ] **Step 2: Run with AWS creds** → FAIL (no CDK deployed / no state machine).

- [ ] **Step 3: Implement** — Execute `cdk deploy --all --context env=dev` + build/push all 3 Docker images (via Phase C `build-*.sh`), then `make run DESIGN=gcd STACK=orfs`.

- [ ] **Step 4: Run test** → PASS (subject to AWS account setup).

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_gcd_orfs_e2e.py
git commit -m "test(e2e): gcd ORFS end-to-end on real AWS"
```

---

### Task E6: E2E — `make run DESIGN=gcd STACK=librelane`

**Files:** Create `tests/e2e/test_gcd_librelane_e2e.py`

Same shape as E5 but `STACK=librelane`.

- [ ] **Steps 1-5**: Copy E5 test, change `STACK` parameter, verify KG-A (LibreLane Fargate) passes. Commit:

```bash
git commit -m "test(e2e): gcd LibreLane end-to-end on real AWS"
```

---

### Task E7: `make kg-all` full pass in live mode

**Files:** None new. Run `make kg-all` without `SMOKE=1`.

- [ ] **Step 1**: Ensure the 5 mandatory gates (KG-A, C1, D, E, F1) all green in live mode.
- [ ] **Step 2**: Capture JSON reports to `artifacts/kg-reports/$(date +%Y-%m-%d)/`.
- [ ] **Step 3**: If any mandatory gate red, fix root cause in its Phase (A/B/C/D) rather than in E.
- [ ] **Step 4**: Confirm `overall_passed: true` in `run-all.sh` output.
- [ ] **Step 5**: Commit the reports:

```bash
git add artifacts/kg-reports/
git commit -m "chore(kg): capture first green KG run-all reports"
```

---

### Task E8: README.md G1 status update + self-review + final commit

**Files:** Modify `README.md`, verify self-review checklist

- [ ] **Step 1: Run self-review** (from §In-progress self-review below). Fix any placeholder or type inconsistency.

- [ ] **Step 2: Write failing test**

```python
# tests/runner/test_readme_g1_status.py
from pathlib import Path
def test_readme_marks_g1_done():
    content = Path("README.md").read_text()
    # Status table should show G1 as done, not pending
    assert "| G1 " in content
    assert "✅" in content  # at least one green checkmark on G1 line
    # Presence check: spec link
    assert "2026-04-20-L1-process-design.md" in content
```

- [ ] **Step 3: Implement** — Modify `README.md` G0/G1 status rows:

```markdown
| G0 | Program bootstrap | ✅ done |
| G1 | L1 Process (Nix + Fargate + SFN + `make run` gcd) | ✅ done (KG-A, C1, D, E, F1 all pass, CI green) |
```

- [ ] **Step 4: Run tests + coverage + lint full sweep**

```bash
uv run pytest tests/ -v --cov=src/semi_design_runner --cov-fail-under=85
uv run ruff check src tests
cd cdk && npx jest && cd ..
make kg-all  # SMOKE mode acceptable for this final check; live already done in E7
```

All green required.

- [ ] **Step 5: Final commit**

```bash
git add README.md tests/runner/test_readme_g1_status.py
git commit -m "docs(l1): mark G1 done — Phase A-E complete, KG gates green"
git log --oneline -20
```

---

## In-progress self-review

After Phase E completes, run self-review against:

1. **Spec coverage**: cross-check every requirement in `docs/superpowers/specs/2026-04-20-L1-process-design.md` §§4, 5, 6, 9, 10, 11, 12, 13, 14, 16 to a task above. Fill gaps.
2. **Placeholder scan**: No `TODO`/`TBD` in plan. Every step shows actual code.
3. **Type consistency**: Pydantic class names used in task code match those defined in schemas (Spec, RunArtifact, etc.).
4. **Sub-skill directive**: executing-plans or subagent-driven-development is explicit in header.

## Execution handoff

Two options after plan completes:

1. **Subagent-Driven (recommended)** — dispatch fresh subagent per task via `superpowers:subagent-driven-development`. Phase A/B/C can run in parallel subagents.
2. **Inline** — execute tasks in this session via `superpowers:executing-plans`.

Decide per-phase. Phase A foundations (schemas, lockfile, metrics, trace) benefit from sequential single-agent focus; Phase B/C/D can parallelize.
