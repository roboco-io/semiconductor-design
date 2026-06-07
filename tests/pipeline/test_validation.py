# tests/pipeline/test_validation.py
import json
from pathlib import Path

from pipeline.validation import candidate_fold_maes, fold_splits, naive_fold_maes

REPO = Path(__file__).resolve().parents[2]


def test_fold_splits_count_and_partition():
    splits = fold_splits(50, k=5, repeats=10, base_seed=0)
    assert len(splits) == 50  # 5 fold × 10 repeat
    tr, va = splits[0]
    assert sorted(tr + va) == list(range(50))  # train+val == 전체
    assert set(tr).isdisjoint(va)  # 겹침 없음
    assert 8 <= len(va) <= 12  # 50/5 ≈ 10


def test_fold_splits_deterministic():
    a = fold_splits(40, k=5, repeats=2, base_seed=7)
    b = fold_splits(40, k=5, repeats=2, base_seed=7)
    assert a == b  # 같은 seed → 같은 split (재현성)


def test_naive_fold_maes_handcomputed():
    rows = [
        {"synth_slack_ns": 0.5, "post_route_slack_ns": 0.2},  # |0.5-0.2|=0.3
        {"synth_slack_ns": 0.0, "post_route_slack_ns": -0.4},  # 0.4
        {"synth_slack_ns": 1.0, "post_route_slack_ns": 1.0},  # 0.0
    ]
    splits = [([0], [1, 2]), ([1], [0, 2])]
    maes = naive_fold_maes(rows, splits)
    assert maes[0] == (0.4 + 0.0) / 2  # val={1,2}
    assert maes[1] == (0.3 + 0.0) / 2  # val={0,2}


def _rows(n=40):
    return [{
        "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
        "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
        "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
        "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
        "path_group": "core_clock",
        "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd",
    } for i in range(n)]


def test_candidate_fold_maes_real_trainpy(tmp_path):
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)  # 5 fold (빠르게)
    maes = candidate_fold_maes(REPO / "train.py", rows, splits, tmp_path / "wd")
    assert len(maes) == 5
    assert all(m >= 0.0 and m != float("inf") for m in maes)


def test_candidate_fold_maes_broken_trainpy_inf(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)
    maes = candidate_fold_maes(broken, rows, splits, tmp_path / "wd2")
    assert all(m == float("inf") for m in maes)  # 모든 fold 실패
