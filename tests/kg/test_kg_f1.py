"""KG-F1 regression — Pre-RunTask budget rejection (zero ECS calls)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "kg" / "kg-f1-prebudget.sh"


def test_kg_f1_smoke_detects_pre_reject() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1"},
        cwd=REPO_ROOT,
    )
    assert r.returncode == 0, r.stderr
    p = json.loads(r.stdout)
    assert p["passed"] is True and p["rejected"] is True
    assert p["ecs_runs"] == 0
