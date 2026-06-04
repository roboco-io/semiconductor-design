import hashlib
from pathlib import Path

from prepare_lib.dataset import flow_lockfile_sha

FIX = Path(__file__).parent / "fixtures"


def test_flow_lockfile_sha_matches_sha256():
    path = FIX / "lockfile.yaml"
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert flow_lockfile_sha(path) == expected
    assert len(flow_lockfile_sha(path)) == 64


def test_flow_lockfile_sha_is_deterministic():
    path = FIX / "lockfile.yaml"
    assert flow_lockfile_sha(path) == flow_lockfile_sha(path)


import json as _json

from prepare_lib.dataset import build_dataset, write_dataset
from prepare_lib.transform import FEATURE_NAMES


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
