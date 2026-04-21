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
