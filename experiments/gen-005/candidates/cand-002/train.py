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
SLACK_IDX = 1  # synth_slack_ns 컬럼 위치 (delta-residual 파라미터화에서 재사용)


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


def _signed_log1p(v: np.ndarray) -> np.ndarray:
    return np.sign(v) * np.log1p(np.abs(v))


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
    total_mean_delay = stages * mean_delay
    delay_spread = max_delay - mean_delay
    delay_ratio = max_delay / (np.abs(mean_delay) + eps)
    slack_per_stage = synth_slack / (stages + eps)
    arrival_per_stage = arrival / (stages + eps)
    criticality = arrival - synth_slack
    ff_pair = start_ff * end_ff
    boundary_ff_count = start_ff + end_ff
    pg_sin = np.sin(path_group)
    pg_cos = np.cos(path_group)

    # aggressive: 스케일 불변 비/잔차 + signed-log 압축 + 고차 교차항.
    # delta label 관찰(드리프트 안정 설계서 강함)을 절대 모델이 흡수하도록 잔차류 feature 강화.
    slack_minus_arrival = synth_slack - arrival
    slack_arrival_ratio = synth_slack / (np.abs(arrival) + eps)
    slack_over_maxdelay = synth_slack / (np.abs(max_delay) + eps)
    spread_ratio = delay_spread / (np.abs(max_delay) + eps)
    est_path_delay = total_mean_delay + delay_spread
    slack_minus_pathdelay = synth_slack - est_path_delay
    log_arrival = _signed_log1p(arrival)
    log_slack = _signed_log1p(synth_slack)
    log_maxdelay = _signed_log1p(max_delay)
    log_total = _signed_log1p(total_mean_delay)
    stages_sq = stages * stages
    crit_per_stage = criticality / (stages + eps)
    slack_x_stages = synth_slack * stages
    maxdelay_x_stages = max_delay * stages

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
        slack_minus_arrival,
        slack_arrival_ratio,
        slack_over_maxdelay,
        spread_ratio,
        est_path_delay,
        slack_minus_pathdelay,
        log_arrival,
        log_slack,
        log_maxdelay,
        log_total,
        stages_sq,
        crit_per_stage,
        slack_x_stages,
        maxdelay_x_stages,
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


def _make_pipe(seed: int) -> Pipeline:
    # aggressive: HGB 손실을 absolute_error로 — val 지표(MAE)와 학습 손실을 정렬.
    hgb = HistGradientBoostingRegressor(
        loss="absolute_error",
        learning_rate=0.05,
        max_iter=450,
        max_leaf_nodes=39,
        l2_regularization=0.03,
        min_samples_leaf=14,
        early_stopping=False,
        random_state=seed,
    )
    hgb2 = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.07,
        max_iter=320,
        max_leaf_nodes=23,
        l2_regularization=0.0,
        min_samples_leaf=20,
        early_stopping=False,
        random_state=seed + 7,
    )
    et = ExtraTreesRegressor(
        n_estimators=320,
        max_features=0.8,
        min_samples_leaf=2,
        bootstrap=False,
        random_state=seed + 17,
        n_jobs=-1,
    )
    ensemble = VotingRegressor(
        estimators=[("hgb_mae", hgb), ("hgb_sq", hgb2), ("et", et)],
        weights=[0.5, 0.2, 0.3],
        n_jobs=-1,
    )
    return Pipeline([
        ("features", FunctionTransformer(add_timing_features, validate=False)),
        ("model", ensemble),
    ])


class BlendedSurrogate(BaseEstimator, RegressorMixin):
    """절대-slack 모델과 delta-residual(post − synth_slack) 모델의 볼록 블렌드.

    관찰 힌트: delta 파라미터화는 드리프트 안정 설계서 강하나 자릿수 드리프트 설계서 약하고,
    held-out 설계별 최선 전략이 갈렸다 → 단일 정답 대신 두 파라미터화를 alpha로 헤지한다.
    alpha는 train 내부 group-disjoint 분할에서 MAE 최소화로 선택(미관측 설계 모사).
    """

    def __init__(self, seed: int = 0, alpha: float = 0.5, slack_idx: int = SLACK_IDX):
        self.seed = seed
        self.alpha = alpha
        self.slack_idx = slack_idx

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        slack = X[:, self.slack_idx]
        self.abs_ = _make_pipe(self.seed)
        self.abs_.fit(X, y)
        self.delta_ = _make_pipe(self.seed + 101)
        self.delta_.fit(X, y - slack)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        slack = X[:, self.slack_idx]
        pa = self.abs_.predict(X)
        pd = slack + self.delta_.predict(X)
        a = float(np.clip(self.alpha, 0.0, 1.0))
        return a * pa + (1.0 - a) * pd


def _select_alpha(X, y, groups, seed: int) -> float:
    # train 내부에서 미관측-설계 모사 분할 후 블렌드 비중 grid search.
    try:
        itr, iva = split(X, y, groups, seed=seed + 1)
        if len(iva) < 3 or len(itr) < 5:
            return 0.5
    except Exception:
        return 0.5

    Xtr, Xva = X[itr], X[iva]
    ytr, yva = y[itr], y[iva]
    slack_va = Xva[:, SLACK_IDX]

    abs_pipe = _make_pipe(seed)
    abs_pipe.fit(Xtr, ytr)
    pa = abs_pipe.predict(Xva)

    delta_pipe = _make_pipe(seed + 101)
    delta_pipe.fit(Xtr, ytr - Xtr[:, SLACK_IDX])
    pd = slack_va + delta_pipe.predict(Xva)

    best_alpha, best_mae = 0.5, float("inf")
    for a in np.linspace(0.0, 1.0, 11):
        mae = mean_absolute_error(yva, a * pa + (1.0 - a) * pd)
        if mae < best_mae:
            best_mae, best_alpha = mae, float(a)
    return best_alpha


def make_model(seed: int = 0, alpha: float = 0.5) -> BlendedSurrogate:
    return BlendedSurrogate(seed=seed, alpha=alpha)


def train_and_eval(X, y, groups, seed: int = 0) -> tuple[object, float]:
    tr, va = split(X, y, groups, seed=seed)
    groups_tr = [groups[i] for i in tr]
    alpha = _select_alpha(X[tr], y[tr], groups_tr, seed=seed)
    model = make_model(seed=seed, alpha=alpha)
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
