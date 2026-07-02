import json
import subprocess
import sys
from pathlib import Path

B1 = Path(__file__).resolve().parents[2] / "pretrain" / "b1_head.py"


def test_b1_cli_contract(tmp_path):
    rows = []
    for i in range(40):
        rows.append({
            "num_stages": 3, "synth_slack_ns": 0.5, "synth_arrival_ns": 1.0,
            "max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1,
            "startpoint_is_ff": 1, "endpoint_is_ff": 1, "path_group": "clk",
            "post_route_slack_ns": 0.1 * i, "group_key": f"d{i % 2}",
            "emb_00": 0.1 * i, "emb_01": -0.05 * i,
        })
    data = tmp_path / "dataset.jsonl"
    data.write_text("\n".join(json.dumps(r) for r in rows))
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(B1), "--data", str(data), "--out", str(out), "--seed", "0"],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    val = json.loads(proc.stdout.strip().splitlines()[-1])
    assert "val_mae" in val and (out / "model.joblib").exists()
