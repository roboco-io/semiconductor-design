# tests/pipeline/test_selection.py
from pipeline.candidate_gen import Candidate
from pipeline.selection import select_winner


def _c(i):
    return Candidate(f"cand-{i}", "moderate", "claude", f"/tmp/{i}/train.py", "diff")


def test_select_min_val_mae():
    results = [(_c(0), 0.5), (_c(1), 0.2), (_c(2), 0.9)]
    winner, val, ranking = select_winner(results)
    assert winner.id == "cand-1" and val == 0.2
    assert [r[0].id for r in ranking] == ["cand-1", "cand-0", "cand-2"]


def test_all_inf_returns_none_winner():
    results = [(_c(0), float("inf")), (_c(1), float("inf"))]
    winner, val, _ = select_winner(results)
    assert winner is None and val == float("inf")


def test_select_winner_ignores_per_seed_third_element():
    results = [
        (_c(0), 0.5, [0.4, 0.5, 0.6]),
        (_c(1), 0.2, [0.1, 0.2, 0.9]),
        (_c(2), float("inf"), [0.1, float("inf")]),
    ]
    winner, val, ranking = select_winner(results)
    assert winner.id == "cand-1" and val == 0.2
    assert ranking[0][0].id == "cand-1"
    assert ranking[0][2] == [0.1, 0.2, 0.9]
