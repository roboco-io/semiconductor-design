"""v4_delta_ratio.py — probe 변형 V4 = V1×V3 조합: 델타 label + 무차원 비율 feature. v3 사본, Operator-owned.

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
        eps = 1e-9
        arrival = abs(float(r["synth_arrival_ns"])) + eps
        max_d = abs(float(r["max_stage_delay_ns"])) + eps
        feats.append([
            float(r["num_stages"]),
            float(r["mean_stage_delay_ns"]) / max_d,
            float(r["synth_slack_ns"]) / arrival,
            float(r["max_stage_delay_ns"]) / arrival,
            float(r["startpoint_is_ff"]),
            float(r["endpoint_is_ff"]),
            float(pg_code[r["path_group"]]),
        ])
    X = np.asarray(feats, dtype=float)
    # V1 축: label을 델타(post_route − synth)로 — 설계 간 오프셋을 label에서 제거.
    # MAE 동일성: |Δ̂−Δ| = |(synth+Δ̂)−post_route| 이므로 절대 slack MAE와 그대로 비교 가능.
    y = np.asarray(
        [float(r[LABEL]) - float(r["synth_slack_ns"]) for r in rows], dtype=float
    )
    groups = [r[GROUP] for r in rows]
    return X, y, groups


def add_timing_features(X: np.ndarray) -> np.ndarray:
    # V3: 무차원 7열(stages, mean/max, slack/arrival, max/arrival, ff, ff, pg) 상호작용.
    X = np.asarray(X, dtype=float)
    stages = X[:, 0]
    mean_over_max = X[:, 1]
    slack_over_arrival = X[:, 2]
    max_over_arrival = X[:, 3]
    start_ff = X[:, 4]
    end_ff = X[:, 5]
    path_group = X[:, 6]

    eps = 1e-9
    extra = np.column_stack([
        mean_over_max * stages,
        slack_over_arrival / (stages + eps),
        max_over_arrival * stages,
        1.0 - mean_over_max,
        slack_over_arrival * max_over_arrival,
        start_ff * end_ff,
        start_ff + end_ff,
        np.sin(path_group),
        np.cos(path_group),
    ])
    return np.hstack([X, extra])


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
    hgb = HistGradientBoostingRegressor(
        learning_rate=0.055,
        max_iter=420,
        max_leaf_nodes=31,
        l2_regularization=0.02,
        min_samples_leaf=12,
        random_state=seed,
    )
    et = ExtraTreesRegressor(
        n_estimators=360,
        max_features=0.85,
        min_samples_leaf=2,
        bootstrap=False,
        random_state=seed + 17,
        n_jobs=-1,
    )
    ensemble = VotingRegressor(
        estimators=[
            ("hgb", hgb),
            ("et", et),
        ],
        weights=[0.58, 0.42],
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
