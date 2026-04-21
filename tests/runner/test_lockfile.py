from pathlib import Path

from semi_design_runner.lockfile import (
    L1_SCOPE_KEYS,
    L3_READINESS_KEYS,
    compute_l1_sha,
    load_lockfile,
    verify_scope,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_lockfile.yaml"


def test_load_lockfile_parses_commit_shas():
    lf = load_lockfile(FIXTURE)
    assert "commit_shas" in lf
    assert lf["commit_shas"]["openroad"] == "abc123"


def test_l1_scope_keys_stable():
    assert L1_SCOPE_KEYS == {"openroad", "librelane", "yosys", "open_pdks"}


def test_l3_readiness_keys_stable():
    assert L3_READINESS_KEYS == {
        "verilator",
        "cocotb",
        "chipyard",
        "gemmini",
        "mlcommons_tiny",
    }


def test_l1_sha_stable_under_l3_drift(tmp_path):
    """Filling L3 SHAs must NOT change l1_lockfile_sha."""
    lf1 = load_lockfile(FIXTURE)
    sha_before = compute_l1_sha(lf1)

    lf2 = dict(lf1)
    lf2["commit_shas"] = dict(lf1["commit_shas"])
    lf2["commit_shas"]["chipyard"] = "newsha"  # L3 SHA added
    lf2["commit_shas"]["verilator"] = "another"
    sha_after = compute_l1_sha(lf2)

    assert sha_before == sha_after


def test_verify_scope_l1_passes_with_l3_null():
    lf = load_lockfile(FIXTURE)
    result = verify_scope(lf, scope="l1")
    assert result["verified"] is True
    assert result["mismatched"] == []
    assert set(result["deferred_l3"]) == L3_READINESS_KEYS
    assert result["scope"] == "l1"
    assert result["l1_lockfile_sha"].startswith("sha256:")


def test_verify_scope_full_fails_when_l3_null():
    lf = load_lockfile(FIXTURE)
    result = verify_scope(lf, scope="full")
    assert result["verified"] is False
    assert set(result["mismatched"]) >= L3_READINESS_KEYS
