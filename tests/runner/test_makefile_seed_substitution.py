"""Verify Makefile `run` target's yq SEED substitution behavior.

Driven by docs/superpowers/plans/2026-05-10-g1-first-smoke.md §2.3 — the G1
smoke needs four seed-varied runs (42 primary, 42 replay, 1337, 31415) sharing
the same Makefile entry point. The actual `make run` body cannot run in CI
(requires AWS creds + Step Functions), so we test the *substitution semantics*
in isolation: copy fixture spec to tmp_path, run the same `yq -i` invocation,
assert the resulting yaml matches expectations. Backward-compat invariant
(SEED omitted → original `seed:` preserved) is the reversible-patch guarantee
called out in INTENT.md `Not` (technical constraint: reversible patch / baseline
not overwritten).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


FIXTURE_SPEC = {
    "version": 1,
    "run_id": "",
    "design": "gcd",
    "stack": "orfs",
    "flow_parameters": {
        "core_utilization": 0.40,
        "place_density": 0.55,
        "clock_period_ps": 5000,
        "global_routing_iterations": 30,
        "timing_driven": True,
        "synth_flatten": False,
    },
    "resource_overrides": {
        "cpu_units": 4096,
        "memory_mb": 16384,
        "ephemeral_storage_gb": 200,
    },
    "compute_budget_usd": 0.50,
    "planned_cost_per_stage_usd": {
        "rtl-build": 0.05,
        "synth": 0.10,
        "pnr": 0.20,
        "signoff": 0.10,
        "metrics": 0.05,
    },
    "seed": 42,
    "l1_lockfile_sha": "",
}


def _yq_available() -> bool:
    return shutil.which("yq") is not None


pytestmark = pytest.mark.skipif(
    not _yq_available(),
    reason="yq binary not available (Makefile run target relies on mikefarah/yq v4+)",
)


@pytest.fixture
def spec_path(tmp_path: Path) -> Path:
    p = tmp_path / "gcd-orfs.yaml"
    p.write_text(yaml.safe_dump(FIXTURE_SPEC, sort_keys=False))
    return p


def _run_yq(expr: str, target: Path) -> None:
    subprocess.run(["yq", "-i", expr, str(target)], check=True)


def test_seed_omitted_preserves_original(spec_path: Path) -> None:
    """SEED= unset → only run_id + l1_lockfile_sha substituted, seed stays 42.

    This is the reversible-patch backward-compat invariant: legacy
    `make run DESIGN=... STACK=... BUCKET=... STATE_MACHINE_ARN=...` callers
    must observe identical yaml output as before the SEED= parameter existed.
    """
    _run_yq('.run_id = "gcd-orfs-1700000000" | .l1_lockfile_sha = "abc123"', spec_path)
    result = yaml.safe_load(spec_path.read_text())
    assert result["seed"] == 42
    assert result["run_id"] == "gcd-orfs-1700000000"
    assert result["l1_lockfile_sha"] == "abc123"


def test_seed_override_writes_int(spec_path: Path) -> None:
    """SEED=1337 → spec yaml `seed` field rewritten to 1337 as integer."""
    _run_yq('.run_id = "gcd-orfs-1700000000-s1337"', spec_path)
    _run_yq(".seed = 1337", spec_path)
    result = yaml.safe_load(spec_path.read_text())
    assert result["seed"] == 1337
    assert isinstance(result["seed"], int)  # schemas.Spec.seed is `int`
    assert result["run_id"].endswith("-s1337")


@pytest.mark.parametrize("seed", [42, 1337, 31415])
def test_g1_smoke_seed_set(spec_path: Path, seed: int) -> None:
    """plan §2.3 frozen seed set {42, 1337, 31415} all substitute cleanly."""
    _run_yq(f".seed = {seed}", spec_path)
    result = yaml.safe_load(spec_path.read_text())
    assert result["seed"] == seed
    # untouched fields stay byte-identical to fixture
    assert result["design"] == "gcd"
    assert result["flow_parameters"]["clock_period_ps"] == 5000
