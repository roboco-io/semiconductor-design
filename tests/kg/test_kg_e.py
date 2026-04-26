"""KG-E regression — Candidates.ddb_write_count < 50 per candidate."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "kg" / "kg-e-ddb-write-amp.sh"


def test_kg_e_smoke_under_limit() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1", "SMOKE_COUNT": "12"},
    )
    assert r.returncode == 0
    assert json.loads(r.stdout)["passed"] is True


def test_kg_e_smoke_over_limit_fails() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1", "SMOKE_COUNT": "80"},
    )
    assert r.returncode == 1
