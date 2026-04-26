"""KG-A regression — LibreLane Fargate gcd ≤30min smoke contract."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "kg" / "kg-a-librelane-fargate.sh"


def test_kg_a_executable() -> None:
    assert SCRIPT.exists() and os.access(SCRIPT, os.X_OK)


def test_kg_a_smoke_emits_required_fields() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1"},
    )
    assert r.returncode == 0, r.stderr
    p = json.loads(r.stdout)
    assert p["mode"] == "smoke" and p["passed"] is True
    for key in ("ephemeral_peak_gb", "image_pull_seconds", "duration_seconds"):
        assert key in p


def test_kg_a_smoke_ephemeral_overflow_fails() -> None:
    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "SMOKE": "1", "SMOKE_EPHEMERAL_GB": "25"},
    )
    assert r.returncode == 1
    assert json.loads(r.stdout)["passed"] is False
