import hashlib
import json as _json
from pathlib import Path

from prepare_lib.dataset import build_dataset, flow_lockfile_sha, write_dataset
from prepare_lib.transform import FEATURE_NAMES

FIX = Path(__file__).parent / "fixtures"


def test_flow_lockfile_sha_matches_sha256():
    path = FIX / "lockfile.yaml"
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert flow_lockfile_sha(path) == expected
    assert len(flow_lockfile_sha(path)) == 64


def test_flow_lockfile_sha_changes_with_content(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("tools:\n  openroad: \"2.0\"\n", encoding="utf-8")
    b.write_text("tools:\n  openroad: \"2.1\"\n", encoding="utf-8")
    sha_a = flow_lockfile_sha(a)
    sha_b = flow_lockfile_sha(b)
    assert sha_a != sha_b
    assert len(sha_a) == 64
    assert len(sha_b) == 64


def test_build_dataset_rows_and_manifest():
    rows, manifest = build_dataset(
        synth_report=FIX / "synth.rpt",
        route_report=FIX / "route.rpt",
        lockfile=FIX / "lockfile.yaml",
        design_id="gcd",
    )
    assert len(rows) == 2  # _0_ and _3_ matched
    assert all(r["group_key"] == "gcd:clk" for r in rows)
    assert manifest["source_design"] == "gcd"
    assert manifest["feature_set"] == FEATURE_NAMES
    assert manifest["label_metric"] == "post_route_slack_ns"
    assert manifest["n_samples"] == 2
    assert len(manifest["flow_lockfile_sha"]) == 64
    assert manifest["id"].startswith("gcd-")


def test_write_dataset_emits_jsonl_and_manifest(tmp_path):
    rows, manifest = build_dataset(
        synth_report=FIX / "synth.rpt",
        route_report=FIX / "route.rpt",
        lockfile=FIX / "lockfile.yaml",
        design_id="gcd",
    )
    write_dataset(rows, manifest, tmp_path)
    lines = (tmp_path / "dataset.jsonl").read_text().splitlines()
    assert len(lines) == 2
    first = _json.loads(lines[0])
    assert "post_route_slack_ns" in first and "group_key" in first
    written_manifest = _json.loads((tmp_path / "manifest.json").read_text())
    assert written_manifest["n_samples"] == 2
