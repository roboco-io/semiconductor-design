from datetime import datetime

import pytest
from pydantic import ValidationError
from semi_design_runner.schemas import (
    ExperimentalParameters,
    FlowParameters,
    Metrics,
    ResourceOverrides,
    RunArtifact,
    Spec,
    StageTiming,
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
    m = Metrics(
        area_um2=12345.0,
        power_mw=None,
        max_freq_mhz=None,
        wns_ns=None,
        tns_ns=None,
        drc_violations=0,
        runtime_s=120.5,
    )
    assert m.area_um2 == 12345.0


def test_run_artifact_clean_status():
    art = RunArtifact(
        run_id="01HABCDEF",
        spec_uri="s3://b/specs/01HABCDEF.yaml",
        status="clean",
        metrics=Metrics(
            area_um2=1.0,
            power_mw=None,
            max_freq_mhz=None,
            wns_ns=None,
            tns_ns=None,
            drc_violations=0,
            runtime_s=10.0,
        ),
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
