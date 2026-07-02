"""encoder 채택 게이트 — spec §6.1~6.4가 임계값의 single source (복사 인용)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split

_STD_MIN = 1e-6       # spec §6.3-①
_COS_MAX = 0.99       # spec §6.3-②
_N_PAIRS = 1000       # spec §6.3-②
TAB_FEATURES = [       # train.py FEATURE_NAMES 복사 인용 (path_group은 ordinal 인코딩)
    "num_stages", "synth_slack_ns", "synth_arrival_ns", "max_stage_delay_ns",
    "mean_stage_delay_ns", "startpoint_is_ff", "endpoint_is_ff", "path_group",
]


def collapse_diagnostics(embs: np.ndarray, seed: int = 0) -> dict:
    med_std = float(np.median(embs.std(axis=0)))
    rng = np.random.default_rng(seed)
    i = rng.integers(0, len(embs), size=_N_PAIRS)
    j = rng.integers(0, len(embs), size=_N_PAIRS)
    a, b = embs[i], embs[j]
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    cos = float(np.mean((a * b).sum(axis=1) / np.clip(denom, 1e-12, None)))
    ok = med_std > _STD_MIN and cos < _COS_MAX
    return {"median_dim_std": med_std, "mean_pairwise_cosine": cos, "pass": ok}


def _split(X, y, groups, seed):
    # train.py split() 방식 복사 인용 — group ≥2면 GroupShuffleSplit, 아니면 fixed-seed random.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        return next(gss.split(X, y, groups=groups))
    idx = np.arange(len(y))
    return train_test_split(idx, test_size=0.25, random_state=seed)


def _probe_mae(rows, cols, seeds) -> float:
    pg = {g: i for i, g in enumerate(sorted({r["path_group"] for r in rows}))}

    def val(r, c):
        return float(pg[r[c]]) if c == "path_group" else float(r[c])

    X = np.array([[val(r, c) for c in cols] for r in rows])
    y = np.array([float(r["post_route_slack_ns"]) for r in rows])
    groups = [r["group_key"] for r in rows]
    maes = []
    for s in seeds:
        tr, va = _split(X, y, groups, s)
        model = LinearRegression().fit(X[tr], y[tr])
        maes.append(mean_absolute_error(y[va], model.predict(X[va])))
    return float(np.median(maes))


def linear_probe(rows: list[dict], seeds=(0, 1, 2, 3, 4)) -> dict:
    emb_cols = sorted(k for k in rows[0] if k.startswith("emb_"))
    emb_mae = _probe_mae(rows, emb_cols, seeds)
    tab_mae = _probe_mae(rows, TAB_FEATURES, seeds)
    return {"emb_median_mae": emb_mae, "tab_median_mae": tab_mae,
            "pass": emb_mae <= tab_mae}


def encoder_verdict(report: dict, diag: dict, probe: dict) -> dict:
    reasons = []
    if not report["best_val_loss"] < report["naive_baseline_loss"]:
        reasons.append("recon: encoder-val loss가 naive 상수 baseline 이상 (spec §6.2)")
    if not diag["pass"]:
        reasons.append("collapse: 붕괴 진단 미달 (spec §6.3)")
    if not probe["pass"]:
        reasons.append("probe: 임베딩 선형 probe가 표형식 초과 (spec §6.4)")
    return {"adopt": not reasons, "reasons": reasons}
