# tests/pipeline/test_holdout.py
import json
import subprocess
import sys
from pathlib import Path

from pipeline.holdout import score_holdout

REPO = Path(__file__).resolve().parents[2]


def _rows(n):
    return [
        {
            "endpoint": f"e{i}",
            "startpoint": f"s{i}",
            "num_stages": 2 + i % 5,
            "synth_slack_ns": 0.4 - (i % 6) * 0.1,
            "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15,
            "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2,
            "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 else "clk2",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1,
            "group_key": "gcd",
        }
        for i in range(n)
    ]


def test_score_holdout_uses_winner_buildxy_and_model(tmp_path):
    # winner train.py = 실제 baseline; 먼저 학습해 model.joblib 생성
    ds = tmp_path / "ds.jsonl"
    ds.write_text("\n".join(json.dumps(r) for r in _rows(40)) + "\n")
    art = tmp_path / "art"
    subprocess.run(
        [
            sys.executable,
            str(REPO / "train.py"),
            "--data",
            str(ds),
            "--out",
            str(art),
            "--seed",
            "0",
        ],
        check=True,
    )
    holdout = tmp_path / "holdout.jsonl"
    holdout.write_text("\n".join(json.dumps(r) for r in _rows(12)) + "\n")
    mae = score_holdout(REPO / "train.py", art / "model.joblib", holdout)
    assert isinstance(mae, float) and mae >= 0.0
