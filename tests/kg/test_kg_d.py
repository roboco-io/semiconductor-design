"""KG-D regression — Spot reclaim recovery rate ≥80%."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "kg" / "kg-d-spot-reclaim.sh"


def test_kg_d_smoke_passes_at_80pct() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1", "SMOKE_RECOVERED": "8", "SMOKE_TOTAL": "10"},
    )
    assert r.returncode == 0
    assert json.loads(r.stdout)["passed"] is True


def test_kg_d_smoke_fails_below_80pct() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1", "SMOKE_RECOVERED": "6", "SMOKE_TOTAL": "10"},
    )
    assert r.returncode == 1
    assert json.loads(r.stdout)["passed"] is False
