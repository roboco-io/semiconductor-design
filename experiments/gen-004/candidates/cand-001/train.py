"""train.py — surrogate 모델 학습 (에이전트가 변형하는 단일 파일, self-contained).

AutoResearch 루프에서 에이전트가 *유일하게 수정*하는 파일. prepare.py의 frozen
dataset.jsonl(8 feature + post_route_slack_ns + group_key)을 읽어 per-endpoint
slack 회귀 모델을 학습하고 단일 val 지표를 출력한다.

계약(고정): --data dataset.jsonl → stdout {"val_mae": <float>} + --out/model.joblib.
제약: 단일 파일 · 고정 예산 · 신규 의존성 금지(sklearn+numpy만) · 단일 지표 최소화.
설계: docs/superpowers/specs/2026-06-06-od4-train-baseline-design.md
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import joblib
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, VotingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

FEATURE_NAMES = [
    "num_stages",
    "synth_slack_ns",
    "synth_arrival_ns",
    "max_stage_delay_ns",
    "mean_stage_delay_ns",
    "startpoint_is_ff",
    "endpoint_is_ff",
    "path_group",
]
LABEL = "post_route_slack_ns"
GROUP = "group_key"


class ResidualRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, base_estimator, anchor_col: int = 1):
        self.base_estimator = base_estimator
        self.anchor_col = anchor_col

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self.estimator_ = clone(self.base_estimator)
        self.estimator_.fit(X, y - X[:, self.anchor_col])
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return X[:, self.anchor_col] + self.estimator_.predict(X)


def load_rows(data_path: str | Path) -> list[dict]:
    path = Path(data_path)
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"{path}:{lineno}: {e.msg}", e.doc, e.pos) from e
    return rows


def build_xy(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    groups_seen = sorted({r["path_group"] for r in rows})
    pg_code = {g: i for i, g in enumerate(groups_seen)}
    feats = []
    for r in rows:
        feats.append([
            float(r["num_stages"]),
            float(r["synth_slack_ns"]),
            float(r["synth_arrival_ns"]),
            float(r["max_stage_delay_ns"]),
            float(r["mean_stage_delay_ns"]),
            float(r["startpoint_is_ff"]),
            float(r["endpoint_is_ff"]),
            float(pg_code[r["path_group"]]),
        ])
    X = np.asarray(feats, dtype=float)
    y = np.asarray([float(r[LABEL]) for r in rows], dtype=float)
    groups = [r[GROUP] for r in rows]
    return X, y, groups


def add_timing_features(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    stages = X[:, 0]
    synth_slack = X[:, 1]
    arrival = X[:, 2]
    max_delay = X[:, 3]
    mean_delay = X[:, 4]
    start_ff = X[:, 5]
    end_ff = X[:, 6]
    path_group = X[:, 7]

    eps = 1e-9
    stage_denom = np.maximum(stages, 1.0)
    total_mean_delay = stages * mean_delay
    delay_spread = max_delay - mean_delay
    delay_ratio = max_delay / (np.abs(mean_delay) + eps)
    slack_per_stage = synth_slack / stage_denom
    arrival_per_stage = arrival / stage_denom
    max_per_stage = max_delay / stage_denom
    mean_per_stage = mean_delay / stage_denom
    criticality = arrival - synth_slack
    normalized_slack = synth_slack / (np.abs(arrival) + np.abs(max_delay) + eps)
    slack_delay_gap = synth_slack - max_delay
    arrival_delay_gap = arrival - total_mean_delay
    ff_pair = start_ff * end_ff
    boundary_ff_count = start_ff + end_ff
    ff_mismatch = np.abs(start_ff - end_ff)
    pg_sin = np.sin(path_group)
    pg_cos = np.cos(path_group)
    log_stages = np.log1p(np.maximum(stages, 0.0))
    log_abs_slack = np.log1p(np.abs(synth_slack)) * np.sign(synth_slack)
    log_abs_arrival = np.log1p(np.abs(arrival)) * np.sign(arrival)

    extra = np.column_stack([
        total_mean_delay,
        delay_spread,
        delay_ratio,
        slack_per_stage,
        arrival_per_stage,
        max_per_stage,
        mean_per_stage,
        criticality,
        normalized_slack,
        slack_delay_gap,
        arrival_delay_gap,
        ff_pair,
        boundary_ff_count,
        ff_mismatch,
        synth_slack * mean_delay,
        synth_slack * max_delay,
        arrival * mean_delay,
        arrival * max_delay,
        stages * max_delay,
        stages * synth_slack,
        delay_spread * stage_denom,
        criticality * mean_delay,
        pg_sin,
        pg_cos,
        log_stages,
        log_abs_slack,
        log_abs_arrival,
    ])
    return np.hstack([X, extra])


def split(X, y, groups, seed: int = 0):
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, va = next(gss.split(X, y, groups=groups))
        return tr, va
    idx = np.arange(len(y))
    tr, va = train_test_split(idx, test_size=0.25, random_state=seed)
    return tr, va


def make_model(seed: int = 0) -> Pipeline:
    hgb_abs = HistGradientBoostingRegressor(
        learning_rate=0.045,
        max_iter=520,
        max_leaf_nodes=31,
        l2_regularization=0.035,
        min_samples_leaf=10,
        validation_fraction=None,
        random_state=seed,
    )
    hgb_delta = HistGradientBoostingRegressor(
        learning_rate=0.04,
        max_iter=460,
        max_leaf_nodes=23,
        l2_regularization=0.08,
        min_samples_leaf=14,
        validation_fraction=None,
        random_state=seed + 11,
    )
    et_abs = ExtraTreesRegressor(
        n_estimators=420,
        max_features=0.72,
        min_samples_leaf=2,
        min_samples_split=4,
        bootstrap=False,
        random_state=seed + 17,
        n_jobs=-1,
    )
    et_delta = ExtraTreesRegressor(
        n_estimators=360,
        max_features=0.65,
        min_samples_leaf=3,
        min_samples_split=6,
        bootstrap=False,
        random_state=seed + 29,
        n_jobs=-1,
    )
    ensemble = VotingRegressor(
        estimators=[
            ("hgb_abs", hgb_abs),
            ("et_abs", et_abs),
            ("hgb_delta", ResidualRegressor(hgb_delta)),
            ("et_delta", ResidualRegressor(et_delta)),
        ],
        weights=[0.34, 0.28, 0.23, 0.15],
        n_jobs=-1,
    )
    return Pipeline([
        ("features", FunctionTransformer(add_timing_features, validate=False)),
        ("model", ensemble),
    ])


def train_and_eval(X, y, groups, seed: int = 0) -> tuple[object, float]:
    tr, va = split(X, y, groups, seed=seed)
    model = make_model(seed)
    model.fit(X[tr], y[tr])
    pred = model.predict(X[va])
    mae = float(mean_absolute_error(y[va], pred))
    return model, mae


@click.command()
@click.option("--data", required=True, type=click.Path(exists=True), help="dataset.jsonl (prepare.py 출력)")
@click.option("--out", required=True, type=click.Path(), help="model.joblib 출력 디렉터리")
@click.option("--seed", default=0, type=int, help="split/모델 시드")
def main(data: str, out: str, seed: int) -> None:
    rows = load_rows(data)
    X, y, groups = build_xy(rows)
    model, mae = train_and_eval(X, y, groups, seed=seed)
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    click.echo(json.dumps({"val_mae": mae}))


if __name__ == "__main__":
    main()
