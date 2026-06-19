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

# prepare.py frozen dataset.jsonl 스키마와 일치 (self-contained 재선언).
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
    # path_group(문자열)을 정렬-안정 ordinal 코드로 인코딩.
    # pg_code는 전체 rows로 만든다; 호출자는 inference 시점 path_group을 제외한 subset으로 build_xy를 부르지 말 것.
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


def _safe_signed_log1p(x: np.ndarray) -> np.ndarray:
    return np.sign(x) * np.log1p(np.abs(x))


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
    stage_denom = stages + eps
    delay_denom = np.abs(mean_delay) + eps
    arrival_denom = np.abs(arrival) + eps
    slack_denom = np.abs(synth_slack) + eps

    total_mean_delay = stages * mean_delay
    delay_spread = max_delay - mean_delay
    delay_ratio = max_delay / delay_denom
    slack_per_stage = synth_slack / stage_denom
    arrival_per_stage = arrival / stage_denom
    criticality = arrival - synth_slack
    ff_pair = start_ff * end_ff
    boundary_ff_count = start_ff + end_ff
    pg_sin = np.sin(path_group)
    pg_cos = np.cos(path_group)

    relative_slack = synth_slack / (np.abs(total_mean_delay) + eps)
    relative_arrival = arrival / (np.abs(total_mean_delay) + eps)
    delay_spread_ratio = delay_spread / delay_denom
    max_delay_per_stage = max_delay / stage_denom
    mean_delay_per_stage = mean_delay / stage_denom
    slack_arrival_ratio = synth_slack / arrival_denom
    criticality_ratio = criticality / (np.abs(criticality) + slack_denom + eps)
    stage_delay_gap = arrival - total_mean_delay
    normalized_gap = stage_delay_gap / (np.abs(arrival) + np.abs(total_mean_delay) + eps)
    slack_delay_margin = synth_slack - delay_spread

    extra = np.column_stack([
        total_mean_delay,
        delay_spread,
        delay_ratio,
        slack_per_stage,
        arrival_per_stage,
        criticality,
        ff_pair,
        boundary_ff_count,
        synth_slack * mean_delay,
        arrival * mean_delay,
        stages * max_delay,
        pg_sin,
        pg_cos,
        relative_slack,
        relative_arrival,
        delay_spread_ratio,
        max_delay_per_stage,
        mean_delay_per_stage,
        slack_arrival_ratio,
        criticality_ratio,
        stage_delay_gap,
        normalized_gap,
        slack_delay_margin,
        _safe_signed_log1p(stages),
        _safe_signed_log1p(synth_slack),
        _safe_signed_log1p(arrival),
        _safe_signed_log1p(max_delay),
        _safe_signed_log1p(mean_delay),
    ])
    return np.hstack([X, extra])


class AnchoredSlackRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, seed: int = 0, absolute_weight: float = 0.78):
        self.seed = seed
        self.absolute_weight = absolute_weight

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        synth_slack = X[:, 1]
        residual_y = y - synth_slack

        self.absolute_model_ = clone(self._make_absolute_model())
        self.residual_model_ = clone(self._make_residual_model())

        self.absolute_model_.fit(X, y)
        self.residual_model_.fit(X, residual_y)

        abs_train = self.absolute_model_.predict(X)
        res_train = synth_slack + self.residual_model_.predict(X)

        blend_train = self.absolute_weight * abs_train + (1.0 - self.absolute_weight) * res_train
        self.bias_ = float(np.median(y - blend_train))

        lo, hi = np.quantile(y, [0.002, 0.998])
        span = max(float(hi - lo), 1e-6)
        self.clip_low_ = float(lo - 0.10 * span)
        self.clip_high_ = float(hi + 0.10 * span)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        synth_slack = X[:, 1]

        abs_pred = self.absolute_model_.predict(X)
        residual_pred = synth_slack + self.residual_model_.predict(X)
        pred = self.absolute_weight * abs_pred + (1.0 - self.absolute_weight) * residual_pred
        pred = pred + self.bias_
        return np.clip(pred, self.clip_low_, self.clip_high_)

    def _make_absolute_model(self) -> VotingRegressor:
        hgb = HistGradientBoostingRegressor(
            learning_rate=0.045,
            max_iter=520,
            max_leaf_nodes=31,
            l2_regularization=0.035,
            min_samples_leaf=14,
            random_state=self.seed,
        )
        et = ExtraTreesRegressor(
            n_estimators=420,
            max_features=0.72,
            min_samples_leaf=3,
            bootstrap=False,
            random_state=self.seed + 17,
            n_jobs=-1,
        )
        return VotingRegressor(
            estimators=[
                ("hgb", hgb),
                ("et", et),
            ],
            weights=[0.62, 0.38],
            n_jobs=-1,
        )

    def _make_residual_model(self) -> VotingRegressor:
        hgb = HistGradientBoostingRegressor(
            learning_rate=0.035,
            max_iter=380,
            max_leaf_nodes=15,
            l2_regularization=0.08,
            min_samples_leaf=18,
            random_state=self.seed + 101,
        )
        et = ExtraTreesRegressor(
            n_estimators=300,
            max_features=0.64,
            min_samples_leaf=5,
            bootstrap=False,
            random_state=self.seed + 131,
            n_jobs=-1,
        )
        return VotingRegressor(
            estimators=[
                ("hgb", hgb),
                ("et", et),
            ],
            weights=[0.70, 0.30],
            n_jobs=-1,
        )


def split(X, y, groups, seed: int = 0):
    # group(=design_id) ≥2면 group-disjoint, 단일 group이면 fixed-seed random.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, va = next(gss.split(X, y, groups=groups))
        return tr, va
    idx = np.arange(len(y))
    tr, va = train_test_split(idx, test_size=0.25, random_state=seed)
    return tr, va


def make_model(seed: int = 0) -> Pipeline:
    return Pipeline([
        ("features", FunctionTransformer(add_timing_features, validate=False)),
        ("model", AnchoredSlackRegressor(seed=seed, absolute_weight=0.78)),
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
