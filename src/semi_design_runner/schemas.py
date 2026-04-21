"""Pydantic v2 schemas for L1 Process layer.

All models inherit from _StrictBase which forbids extra fields (Codex review
requirement). This prevents L2/L3 breaking-change drift through arbitrary dict
injection. Spec.parameters is broken into tagged sub-models (FlowParameters,
ResourceOverrides, ExperimentalParameters) per spec §4.1.
"""
from __future__ import annotations

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
