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
        allowed = ", ".join(sorted(G1_ALLOWED_DESIGNS))
        raise RejectedNotInG1Scope(
            f"design={spec.design} is not in G1 scope; "
            f"allowed: [{allowed}]"
        )
