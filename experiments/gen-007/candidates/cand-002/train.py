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

# synth_slack 컬럼은 add_timing_features 가 원본 8열을 hstack 선두에 보존하므로
# 변형 후에도 index 1 로 고정된다 (DeltaRegressor anchor / 스케일 압축 기준).
SYNTH_SLACK_IDX = 1


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
    # 부호 보존 로그 압축: 설계별로 자릿수가 다른 절대 스케일 신호를
    # log 영역으로 눌러 미관측 설계 전이 시 절대 스케일 의존을 줄인다.
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
    abs_mean = np.abs(mean_delay) + eps
    abs_arrival = np.abs(arrival) + eps

    # ── 설계-불변(상대) 신호: 절대 ns 대신 비율/정규화로 설계간 자릿수 차이를 흡수 ──
    total_mean_delay = stages * mean_delay
    delay_spread = max_delay - mean_delay
    delay_ratio = max_delay / abs_mean
    spread_ratio = delay_spread / abs_mean          # 절대 스케일 무관 변동성
    slack_per_stage = synth_slack / (stages + eps)
    arrival_per_stage = arrival / (stages + eps)
    slack_frac = synth_slack / abs_arrival           # arrival 대비 여유 비율 (스케일 불변)
    max_delay_frac = max_delay / abs_arrival          # critical stage 점유율
    criticality = arrival - synth_slack
    crit_frac = criticality / abs_arrival
    ff_pair = start_ff * end_ff
    boundary_ff_count = start_ff + end_ff
    pg_sin = np.sin(path_group)
    pg_cos = np.cos(path_group)

    # ── 부호 보존 로그 압축: 절대 스케일 의존 축소 (LODO 전이 목표) ──
    log_slack = _signed_log1p(synth_slack)
    log_arrival = _signed_log1p(arrival)
    log_max_delay = _signed_log1p(max_delay)
    log_mean_delay = _signed_log1p(mean_delay)
    log_crit = _signed_log1p(criticality)

    extra = np.column_stack([
        total_mean_delay,
        delay_spread,
        delay_ratio,
        spread_ratio,
        slack_per_stage,
        arrival_per_stage,
        slack_frac,
        max_delay_frac,
        criticality,
        crit_frac,
        ff_pair,
        boundary_ff_count,
        pg_sin,
        pg_cos,
        log_slack,
        log_arrival,
        log_max_delay,
        log_mean_delay,
        log_crit,
    ])
    return np.hstack([X, extra])


class DeltaRegressor(BaseEstimator, RegressorMixin):
    """post_route_slack_ns 를 직접 예측하지 않고 synth_slack 대비 *잔차(드리프트)* 를 학습.

    절대 slack 은 설계마다 자릿수로 다르지만 (synth → post-route) 드리프트는 더 설계-안정적이라는
    probe 관찰을 활용. 예측은 base.predict(X) + synth_slack 으로 원래 ns 단위 복원하므로 val_mae
    계약(post_route_slack_ns 의 MAE) 불변.
    """

    def __init__(self, base=None, anchor_idx: int = SYNTH_SLACK_IDX):
        self.base = base
        self.anchor_idx = anchor_idx

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        anchor = X[:, self.anchor_idx]
        self.base_ = clone(self.base)
        self.base_.fit(X, np.asarray(y, dtype=float) - anchor)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return self.base_.predict(X) + X[:, self.anchor_idx]


def split(X, y, groups, seed: int = 0):
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, va = next(gss.split(X, y, groups=groups))
        return tr, va
    idx = np.arange(len(y))
    tr, va = train_test_split(idx, test_size=0.25, random_state=seed)
    return tr, va


def make_model(seed: int = 0) -> Pipeline:
    # MAE 목표 정렬: absolute_error 손실 HGB 를 주축으로, 분산 감소용 보조 학습기 혼합.
    hgb_l1 = HistGradientBoostingRegressor(
        loss="absolute_error",
        learning_rate=0.05,
        max_iter=500,
        max_leaf_nodes=31,
        l2_regularization=0.05,
        min_samples_leaf=15,
        random_state=seed,
    )
    hgb_l2 = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.07,
        max_iter=350,
        max_leaf_nodes=15,
        l2_regularization=0.1,
        min_samples_leaf=20,
        random_state=seed + 5,
    )
    et = ExtraTreesRegressor(
        n_estimators=400,
        max_features=0.7,
        min_samples_leaf=3,
        bootstrap=False,
        random_state=seed + 17,
        n_jobs=-1,
    )
    ensemble = VotingRegressor(
        estimators=[
            ("hgb_l1", hgb_l1),
            ("hgb_l2", hgb_l2),
            ("et", et),
        ],
        weights=[0.5, 0.25, 0.25],
        n_jobs=-1,
    )
    delta = DeltaRegressor(base=ensemble, anchor_idx=SYNTH_SLACK_IDX)
    return Pipeline([
        ("features", FunctionTransformer(add_timing_features, validate=False)),
        ("model", delta),
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
