"""데이터셋 조립 + manifest + I/O (flow_lockfile_sha 재현성 앵커)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prepare_lib.report import parse_report
from prepare_lib.transform import FEATURE_NAMES, LABEL_NAME, group_key, join_paths


def flow_lockfile_sha(lockfile_path: str | Path) -> str:
    return hashlib.sha256(Path(lockfile_path).read_bytes()).hexdigest()


def build_dataset(
    synth_report: str | Path,
    route_report: str | Path,
    lockfile: str | Path,
    design_id: str,
) -> tuple[list[dict], dict]:
    synth = parse_report(Path(synth_report).read_text())
    route = parse_report(Path(route_report).read_text())
    rows = join_paths(synth, route)
    for r in rows:
        r["group_key"] = group_key(r["path_group"], design_id)
    sha = flow_lockfile_sha(lockfile)
    manifest = {
        "id": f"{design_id}-{sha[:12]}",
        "source_design": design_id,
        "feature_set": FEATURE_NAMES,
        "label_metric": LABEL_NAME,
        "flow_lockfile_sha": sha,
        "n_samples": len(rows),
    }
    return rows, manifest


def write_dataset(rows: list[dict], manifest: dict, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dataset.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
