"""train.py — surrogate 모델 학습 (에이전트가 변형하는 단일 파일, self-contained).

AutoResearch 루프에서 에이전트가 *유일하게 수정*하는 파일. prepare.py의 frozen
dataset.jsonl(8 feature + post_route_slack_ns + group_key)을 읽어 per-endpoint
slack 회귀 모델을 학습하고 단일 val 지표를 출력한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import joblib
import numpy as np
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
    VotingRegressor,
)
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
        feats.append(
            [
                float(r["num_stages"]),
                float(r["synth_slack_ns"]),
                float(r["synth_arrival_ns"]),
                float(r["max_stage_delay_ns"]),
                float(r["mean_stage_delay_ns"]),
                float(r["startpoint_is_ff"]),
                float(r["endpoint_is_ff"]),
                float(pg_code[r["path_group"]]),
            ]
        )
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
    safe_stages = np.maximum(stages, 1.0)
    delay_spread = max_delay - mean_delay
    total_mean_delay = stages * mean_delay
    required_time_proxy = arrival - synth_slack
    slack_per_stage = synth_slack / (safe_stages + eps)
    arrival_per_stage = arrival / (safe_stages + eps)
    max_per_stage = max_delay / (safe_stages + eps)
    mean_per_stage = mean_delay / (safe_stages + eps)
    delay_ratio = max_delay / (np.abs(mean_delay) + eps)
    spread_ratio = delay_spread / (np.abs(max_delay) + np.abs(mean_delay) + eps)
    ff_pair = start_ff * end_ff
    ff_count = start_ff + end_ff
    ff_mismatch = np.abs(start_ff - end_ff)

    abs_slack = np.abs(synth_slack)
    abs_arrival = np.abs(arrival)
    log_stages = np.log1p(np.maximum(stages, 0.0))
    log_abs_slack = np.log1p(abs_slack)
    log_abs_arrival = np.log1p(abs_arrival)
    log_max_delay = np.log1p(np.maximum(max_delay, 0.0))
    log_mean_delay = np.log1p(np.maximum(mean_delay, 0.0))

    pg_angle = path_group * 0.73
    pg_sin = np.sin(pg_angle)
    pg_cos = np.cos(pg_angle)
    pg_bucket = np.mod(path_group, 5.0)

    extra = np.column_stack(
        [
            total_mean_delay,
            delay_spread,
            delay_ratio,
            spread_ratio,
            slack_per_stage,
            arrival_per_stage,
            max_per_stage,
            mean_per_stage,
            required_time_proxy,
            ff_pair,
            ff_count,
            ff_mismatch,
            synth_slack * mean_delay,
            synth_slack * max_delay,
            arrival * mean_delay,
            arrival * max_delay,
            stages * max_delay,
            stages * mean_delay,
            required_time_proxy * mean_delay,
            required_time_proxy * max_delay,
            synth_slack * ff_pair,
            arrival * ff_pair,
            delay_spread * ff_count,
            abs_slack,
            abs_arrival,
            synth_slack * synth_slack,
            arrival * arrival,
            max_delay * max_delay,
            mean_delay * mean_delay,
            log_stages,
            log_abs_slack,
            log_abs_arrival,
            log_max_delay,
            log_mean_delay,
            pg_sin,
            pg_cos,
            pg_bucket,
        ]
    )
    return np.nan_to_num(np.hstack([X, extra]), copy=False, nan=0.0, posinf=1e6, neginf=-1e6)


def split(X: np.ndarray, y: np.ndarray, groups: list[str], seed: int = 0):
    if len(y) < 4:
        idx = np.arange(len(y))
        return idx, idx

    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, va = next(gss.split(X, y, groups=groups))
        if len(tr) and len(va):
            return tr, va

    idx = np.arange(len(y))
    tr, va = train_test_split(idx, test_size=0.25, random_state=seed)
    return tr, va


def make_model(seed: int = 0) -> Pipeline:
    hgb = HistGradientBoostingRegressor(
        loss="absolute_error",
        learning_rate=0.045,
        max_iter=520,
        max_leaf_nodes=31,
        min_samples_leaf=10,
        l2_regularization=0.015,
        random_state=seed,
    )
    et = ExtraTreesRegressor(
        n_estimators=520,
        max_features=0.72,
        min_samples_leaf=2,
        min_samples_split=3,
        bootstrap=False,
        random_state=seed + 17,
        n_jobs=-1,
    )
    rf = RandomForestRegressor(
        n_estimators=260,
        max_features=0.7,
        min_samples_leaf=2,
        bootstrap=True,
        random_state=seed + 29,
        n_jobs=-1,
    )
    gbr = GradientBoostingRegressor(
        loss="absolute_error",
        learning_rate=0.045,
        n_estimators=320,
        max_depth=3,
        min_samples_leaf=5,
        subsample=0.86,
        random_state=seed + 41,
    )
    ensemble = VotingRegressor(
        estimators=[
            ("hgb", hgb),
            ("et", et),
            ("rf", rf),
            ("gbr", gbr),
        ],
        weights=[0.34, 0.34, 0.17, 0.15],
        n_jobs=-1,
    )
    return Pipeline(
        [
            ("features", FunctionTransformer(add_timing_features, validate=False)),
            ("model", ensemble),
        ]
    )


def train_and_eval(X: np.ndarray, y: np.ndarray, groups: list[str], seed: int = 0) -> tuple[object, float]:
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
