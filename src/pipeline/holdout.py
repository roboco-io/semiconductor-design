"""holdout — winner train.py의 build_xy + 저장된 model로 held-out MAE 재채점.

val-gaming 방어(설계 §6): 후보가 미관측한 held-out에서 winner를 재평가.
winner train.py를 모듈로 로드해 그 build_xy(frozen 계약)를 재사용한다.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import joblib
from sklearn.metrics import mean_absolute_error


def _load_module(train_py: Path):
    spec = importlib.util.spec_from_file_location("winner_train", str(train_py))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score_holdout(train_py: Path, model_path: Path, holdout: Path) -> float:
    mod = _load_module(Path(train_py))
    rows = [json.loads(line) for line in Path(holdout).read_text().splitlines() if line.strip()]
    X, y, _ = mod.build_xy(rows)
    model = joblib.load(model_path)
    return float(mean_absolute_error(y, model.predict(X)))
