"""InitGeneration Lambda (L1 Process — WorkflowStack).

L1 always runs with a single generation (N=0) per L1 spec §6.1. L2/L3 will
override this function to emit multi-candidate generations; for G1 we emit
exactly one candidate so the downstream SFN Map state has a single
iteration and the per-candidate ECS task shape is exercised end-to-end.
"""

from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    spec = event.get("spec", event)
    run_id = spec["run_id"]
    return {
        "run_id": run_id,
        "generation": 0,
        "candidates": [
            {
                "run_id": run_id,
                "gen": 0,
                "cand": 0,
                "spec": spec,
            },
        ],
    }
