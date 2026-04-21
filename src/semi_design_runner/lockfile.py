"""Lockfile verification with L1/L3-readiness scope separation.

The L1 scope hash must be invariant under L3-readiness SHA drift — that is,
filling `verilator` or `chipyard` SHAs must NOT change l1_lockfile_sha, which
serves as the cache key for L1 runs. See spec §9.1 canonical-yaml rule.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Literal

import yaml

L1_SCOPE_KEYS: set[str] = {"openroad", "librelane", "yosys", "open_pdks"}
L3_READINESS_KEYS: set[str] = {
    "verilator",
    "cocotb",
    "chipyard",
    "gemmini",
    "mlcommons_tiny",
}


def load_lockfile(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def canonical_yaml(data: dict[str, Any]) -> str:
    """Sort keys and drop null values so L3 nulls do not affect hash."""
    return yaml.safe_dump(
        _strip_nulls(data),
        sort_keys=True,
        default_flow_style=False,
    )


def _strip_nulls(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_nulls(v) for v in obj]
    return obj


def _project_l1(lockfile: dict[str, Any]) -> dict[str, Any]:
    """Keep only L1-scope commit_shas + container_digests + pdk_digests."""
    return {
        "version": lockfile["version"],
        "commit_shas": {k: v for k, v in lockfile["commit_shas"].items() if k in L1_SCOPE_KEYS},
        "container_digests": lockfile["container_digests"],
        "pdk_digests": lockfile.get("pdk_digests", {}),
    }


def compute_l1_sha(lockfile: dict[str, Any]) -> str:
    projected = _project_l1(lockfile)
    digest = hashlib.sha256(canonical_yaml(projected).encode()).hexdigest()
    return f"sha256:{digest}"


def verify_scope(
    lockfile: dict[str, Any],
    scope: Literal["l1", "full"] = "l1",
) -> dict[str, Any]:
    commit_shas = lockfile["commit_shas"]
    if scope == "l1":
        check_keys = L1_SCOPE_KEYS
    else:
        check_keys = L1_SCOPE_KEYS | L3_READINESS_KEYS
    mismatched = [k for k in check_keys if commit_shas.get(k) in (None, "")]
    deferred = sorted(k for k in L3_READINESS_KEYS if commit_shas.get(k) in (None, ""))
    return {
        "verified": len(mismatched) == 0,
        "mismatched": sorted(mismatched),
        "deferred_l3": deferred if scope == "l1" else [],
        "scope": scope,
        "l1_lockfile_sha": compute_l1_sha(lockfile),
    }
