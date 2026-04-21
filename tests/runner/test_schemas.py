import pytest
from pydantic import ValidationError
from semi_design_runner.schemas import (
    ExperimentalParameters,
    FlowParameters,
    ResourceOverrides,
)
from semi_design_runner.schemas import Spec


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
