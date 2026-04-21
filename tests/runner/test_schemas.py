import pytest
from pydantic import ValidationError
from semi_design_runner.schemas import (
    ExperimentalParameters,
    FlowParameters,
    ResourceOverrides,
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
