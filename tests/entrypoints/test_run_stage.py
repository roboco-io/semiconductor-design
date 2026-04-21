"""Contract tests for docker/entrypoints/run-stage.sh.

These tests exercise the shell script directly (no docker build required),
so they run fast on every commit. They verify:

1. `SIMULATE_SPOT_RECLAIM=1` causes exit code 143 (KG-D contract, spec §10).
2. Missing required env vars cause exit 2 with a clear error.
3. The staging layout under $OUTPUT_LOCAL matches spec §4.3
   (`runs/{run_id}/staging/{stage}/`).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ENTRYPOINT = Path(__file__).resolve().parents[2] / "docker" / "entrypoints" / "run-stage.sh"


def _run(env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(ENTRYPOINT)],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_simulate_spot_reclaim_exits_143(tmp_path: Path) -> None:
    env = {
        "RUN_ID": "01HTEST",
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{tmp_path}/in",
        "OUTPUT_S3_URI": f"file://{tmp_path}/out",
        "SIMULATE_SPOT_RECLAIM": "1",
        "SIMULATE_SPOT_RECLAIM_DELAY_S": "0",  # no sleep in tests
        "STAGE_COMMAND": "echo should-not-run",
    }
    r = _run(env)
    assert r.returncode == 143, r.stderr
    assert "SIMULATE_SPOT_RECLAIM" in r.stderr


def test_missing_run_id_exits_2(tmp_path: Path) -> None:
    env = {
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{tmp_path}",
        "OUTPUT_S3_URI": f"file://{tmp_path}",
        "STAGE_COMMAND": "true",
    }
    r = _run(env)
    assert r.returncode == 2
    assert "RUN_ID" in r.stderr


def test_staging_layout_created(tmp_path: Path) -> None:
    in_dir = tmp_path / "in"
    in_dir.mkdir()
    out_dir = tmp_path / "out"
    env = {
        "RUN_ID": "01HTEST",
        "STAGE": "synth",
        "INPUT_S3_URI": f"file://{in_dir}",
        "OUTPUT_S3_URI": f"file://{out_dir}",
        "SIMULATE_SPOT_RECLAIM": "0",
        "STAGE_COMMAND": "echo hello > $STAGE_WORK_DIR/marker.txt",
    }
    r = _run(env)
    assert r.returncode == 0, r.stderr
    # Spec §4.3: staging layout must be runs/{run_id}/staging/{stage}/
    assert (out_dir / "runs" / "01HTEST" / "staging" / "synth" / "marker.txt").exists()
