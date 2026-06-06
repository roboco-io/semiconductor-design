# tests/pipeline/test_runner.py
import json
from pathlib import Path

from pipeline.runner import run_candidate

REPO = Path(__file__).resolve().parents[2]


def _dataset(tmp_path):
    rows = []
    for i in range(40):
        rows.append({
            "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
            "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 else "clk2",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd" if i % 2 else "ibex",
        })
    p = tmp_path / "ds.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_run_candidate_returns_val_mae(tmp_path):
    # 실제 baseline train.py를 후보로 사용 (계약 검증)
    val = run_candidate(REPO / "train.py", _dataset(tmp_path), tmp_path / "art", seed=0)
    assert isinstance(val, float) and val >= 0.0
    assert (tmp_path / "art" / "model.joblib").exists()


def test_run_candidate_broken_returns_inf(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    val = run_candidate(broken, _dataset(tmp_path), tmp_path / "art2", seed=0)
    assert val == float("inf")
