"""runner — 후보 train.py를 subprocess로 실행하고 val_mae를 파싱."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_candidate(train_py: Path, dataset: Path, out_dir: Path, seed: int = 0) -> float:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(train_py), "--data", str(dataset),
         "--out", str(out_dir), "--seed", str(seed)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return float("inf")
    for line in reversed(proc.stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return float(json.loads(line)["val_mae"])
            except (ValueError, KeyError):
                continue
    return float("inf")


def run_all(candidates, dataset: Path, out_root: Path, seed: int = 0):
    results = []
    for c in candidates:
        art = Path(out_root) / c.id / "art"
        val = run_candidate(Path(c.src_path), dataset, art, seed=seed)
        results.append((c, val))
    return results
