"""ValidateSpec Lambda (L1 Process — WorkflowStack).

Rejects any Spec whose ``design`` is not in the G1 allowed-list. Raises
``RejectedNotInG1Scope`` so the Step Functions state machine surfaces
``errorType: "RejectedNotInG1Scope"`` in execution history — this is the
exact string the Python runner's Phase A tests assert against (see
``src/semi_design_runner/validator.py`` and L1 spec §4.2 error taxonomy).
"""

from __future__ import annotations

import os
from typing import Any


class RejectedNotInG1Scope(Exception):
    """Spec.design is not allowed in G1 scope.

    Kept as a module-level class (not an import from the Python runner) so
    the Lambda bundle stays free of the ``semi_design_runner`` package — the
    Lambda is shipped as a single-file asset via ``lambda.Code.fromAsset``.
    """


ALLOWED_DESIGN = os.environ.get("G1_ALLOWED_DESIGN", "gcd")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    spec = event.get("spec", event)
    design = spec.get("design")
    if design != ALLOWED_DESIGN:
        raise RejectedNotInG1Scope(
            f"design={design} is not in G1 scope; allowed: [{ALLOWED_DESIGN}]"
        )
    # Pass the spec through so the downstream InitGeneration + Map state
    # receive the validated payload unchanged.
    return {"ok": True, "spec": spec}
