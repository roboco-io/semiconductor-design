import pytest
from semi_design_runner.schemas import Spec, FlowParameters
from semi_design_runner.validator import (
    RejectedNotInG1Scope,
    validate_spec_for_g1,
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
