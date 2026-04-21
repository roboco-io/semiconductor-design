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
