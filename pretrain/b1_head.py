"""B1 — 새 표현 naive baseline: 임베딩만 + 사람이 1회 작성한 단순 head (spec §7).

train.py와 동일 CLI 계약 — 기존 runner/validation 게이트가 그대로 평가한다.
사람 소유 · 변형 금지(B1은 고정 비교점).
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def load_rows(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def build_xy(rows):
    cols = sorted(k for k in rows[0] if k.startswith("emb_"))
    X = np.array([[float(r[c]) for c in cols] for r in rows])
    y = np.array([float(r["post_route_slack_ns"]) for r in rows])
    return X, y, [r["group_key"] for r in rows]


def split(X, y, groups, seed=0):
    # train.py split() 복사 인용 — 동일 프로토콜 비교 보장.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        return next(gss.split(X, y, groups=groups))
    idx = np.arange(len(y))
    return train_test_split(idx, test_size=0.25, random_state=seed)


@click.command()
@click.option("--data", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--seed", default=0, type=int)
def main(data, out, seed):
    rows = load_rows(data)
    X, y, groups = build_xy(rows)
    tr, va = split(X, y, groups, seed)
    model = Ridge(alpha=1.0).fit(X[tr], y[tr])
    mae = float(mean_absolute_error(y[va], model.predict(X[va])))
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_dir / "model.joblib")
    click.echo(json.dumps({"val_mae": mae}))


if __name__ == "__main__":
    main()
