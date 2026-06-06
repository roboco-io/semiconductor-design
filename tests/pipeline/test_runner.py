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


from pipeline.runner import run_candidate_multiseed


def test_multiseed_returns_median_and_per_seed(tmp_path):
    agg, per_seed = run_candidate_multiseed(
        REPO / "train.py", _dataset(tmp_path), tmp_path / "ms", seeds=(0, 1, 2)
    )
    assert isinstance(agg, float) and agg >= 0.0
    assert len(per_seed) == 3 and all(v >= 0.0 for v in per_seed)
    assert agg == sorted(per_seed)[1]  # median of 3 == middle value


def test_multiseed_any_inf_disqualifies(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    agg, per_seed = run_candidate_multiseed(
        broken, _dataset(tmp_path), tmp_path / "ms2", seeds=(0, 1, 2, 3, 4)
    )
    assert agg == float("inf")
    assert per_seed[-1] == float("inf")


from pipeline.candidate_gen import Candidate
from pipeline.runner import run_all


def test_run_all_returns_median_triples(tmp_path):
    ds = _dataset(tmp_path)
    src = REPO / "train.py"
    cands = [Candidate("cand-0", "moderate", "claude", str(src), "diff")]
    results = run_all(cands, ds, tmp_path / "root", seeds=(0, 1, 2))
    assert len(results) == 1
    c, median_val, per_seed = results[0]
    assert c.id == "cand-0"
    assert isinstance(median_val, float) and median_val >= 0.0
    assert len(per_seed) == 3


def test_multiseed_short_circuits_on_first_inf(tmp_path, monkeypatch):
    import pipeline.runner as R
    calls = []

    def fake_run_candidate(train_py, dataset, out_dir, seed=0, timeout=300):
        calls.append(seed)
        return float("inf") if seed == 1 else 0.2

    monkeypatch.setattr(R, "run_candidate", fake_run_candidate)
    agg, per_seed = R.run_candidate_multiseed(
        Path("/x/train.py"), Path("/x/ds.jsonl"), tmp_path / "ms3", seeds=(0, 1, 2, 3, 4)
    )
    assert agg == float("inf")
    assert calls == [0, 1]
