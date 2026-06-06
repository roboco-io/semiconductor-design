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
    # 신뢰 경계: exec_module은 train.py의 최상위 코드를 import 시점에 실행한다.
    # 에이전트 생성 코드이므로 side effect(파일 쓰기, 네트워크 등)가 포함될 수 있음.
    # MVP에서는 허용 (AutoResearch 루프의 본질적 위험), Operator 승인 후에만 호출할 것.
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
