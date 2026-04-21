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
    """Internal base for L1 schemas.

    Rejects unknown keys to prevent silent layer drift. Do not instantiate directly.
    """

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


# Terminal + in-progress run states. Producers:
#   clean/drc_fail/lvs_fail/sta_fail/tool_crash ← Fargate runner (Docker ENTRYPOINT)
#   spot_reclaimed_max ← KG-D deterministic SIMULATE_SPOT_RECLAIM path
#   rejected_not_in_g1 ← Task A13 ValidateSpec (design ∉ G1 scope)
#   budget_exceeded    ← Task A12 cost guard (F1 pre-run or F2 in-run)
#   in_progress        ← initial DDB write before any stage completes
RunStatus = Literal[
    "clean",
    "drc_fail",
    "lvs_fail",
    "sta_fail",
    "tool_crash",
    "spot_reclaimed_max",
    "rejected_not_in_g1",
    "budget_exceeded",
    "in_progress",
]


class StageTiming(_StrictBase):
    """Per-stage Fargate timing + cost. One entry per completed stage in RunArtifact.cost_breakdown."""

    stage: StageName
    started_at: datetime
    ended_at: datetime
    exit_code: int
    cost_usd: float
    fargate_vcpu: int
    fargate_memory_mb: int


class Metrics(_StrictBase):
    """Signoff metrics parsed from .rpt/.def. All-or-nothing: constructed only when signoff
    completes. Partial/crashed runs set RunArtifact.metrics=None (not a Metrics with sentinels)."""

    area_um2: float
    power_mw: float | None
    max_freq_mhz: float | None
    wns_ns: float | None
    tns_ns: float | None
    drc_violations: int
    runtime_s: float


class RunArtifact(_StrictBase):
    """L1.run(spec_uri) output.

    Invariants:
      - metrics_uri is ALWAYS a valid S3 key; metrics is the inlined mirror or None if the
        run crashed pre-signoff.
      - ended_at=None means the run is still executing (status="in_progress"). No default,
        so callers must explicitly pass None for the in-flight case.
      - full_lockfile_sha=None when L3-readiness scope is out of bounds (default path).
    """

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
