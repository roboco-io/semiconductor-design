import numpy as np

from pretrain_lib.encoder_gates import collapse_diagnostics, encoder_verdict, linear_probe


def test_collapse_detects_constant_embeddings():
    embs = np.ones((50, 8))
    d = collapse_diagnostics(embs)
    assert not d["pass"]


def test_collapse_passes_diverse_embeddings():
    rng = np.random.default_rng(0)
    d = collapse_diagnostics(rng.normal(size=(50, 8)))
    assert d["pass"] and d["median_dim_std"] > 1e-6 and d["mean_pairwise_cosine"] < 0.99


def _rows(n=120, emb_informative=True):
    rng = np.random.default_rng(1)
    rows = []
    for i in range(n):
        y = float(rng.normal())
        emb = [y + rng.normal(0, 0.01), rng.normal()] if emb_informative \
            else [rng.normal(), rng.normal()]
        rows.append({
            "num_stages": 3, "synth_slack_ns": rng.normal(), "synth_arrival_ns": 1.0,
            "max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1,
            "startpoint_is_ff": 1, "endpoint_is_ff": 1, "path_group": "clk",
            "post_route_slack_ns": y, "group_key": f"d{i % 3}",
            "emb_00": emb[0], "emb_01": emb[1],
        })
    return rows


def test_linear_probe_informative_embeddings_pass():
    p = linear_probe(_rows(emb_informative=True))
    assert p["pass"] and p["emb_median_mae"] <= p["tab_median_mae"]


def test_verdict_requires_all_gates():
    report = {"best_val_loss": 0.5, "naive_baseline_loss": 1.0}
    diag_ok = {"pass": True}
    probe_ok = {"pass": True}
    assert encoder_verdict(report, diag_ok, probe_ok)["adopt"]
    assert not encoder_verdict(
        {"best_val_loss": 1.5, "naive_baseline_loss": 1.0}, diag_ok, probe_ok
    )["adopt"]
    assert not encoder_verdict(report, {"pass": False}, probe_ok)["adopt"]
    assert not encoder_verdict(report, diag_ok, {"pass": False})["adopt"]
