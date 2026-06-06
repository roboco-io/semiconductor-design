# tests/train/test_train.py
import json
import subprocess
import sys
from pathlib import Path

import pytest

import train

REPO = Path(__file__).resolve().parents[2]


def _write_dataset(path: Path, n: int = 40, groups=("gcd", "ibex")) -> Path:
    """결정론적 합성 dataset.jsonl (학습 가능한 규모, group 2개)."""
    rows = []
    for i in range(n):
        g = groups[i % len(groups)]
        slack = 0.5 - (i % 7) * 0.1  # 일부 음수(violation) 포함
        rows.append({
            "endpoint": f"ep_{i}",
            "startpoint": f"sp_{i}",
            "num_stages": 2 + (i % 5),
            "synth_slack_ns": 0.4 - (i % 6) * 0.1,
            "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15,
            "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2,
            "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 == 0 else "clk2",
            "post_route_slack_ns": slack,
            "group_key": g,
        })
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def test_load_rows_reads_jsonl(tmp_path):
    p = _write_dataset(tmp_path / "ds.jsonl", n=10)
    rows = train.load_rows(p)
    assert len(rows) == 10
    assert rows[0]["post_route_slack_ns"] == 0.5


def test_build_xy_shapes_and_label(tmp_path):
    rows = train.load_rows(_write_dataset(tmp_path / "ds.jsonl", n=12))
    X, y, groups = train.build_xy(rows)
    assert X.shape == (12, len(train.FEATURE_NAMES))
    assert y.shape == (12,)
    assert len(groups) == 12
    # path_group은 숫자 인코딩되어야 한다 (모델 입력은 float 행렬)
    assert X.dtype.kind in "fi"


def test_group_split_is_disjoint(tmp_path):
    rows = train.load_rows(_write_dataset(tmp_path / "ds.jsonl", n=40))
    X, y, groups = train.build_xy(rows)
    tr, va = train.split(X, y, groups, seed=0)
    tr_groups = {groups[i] for i in tr}
    va_groups = {groups[i] for i in va}
    assert tr_groups.isdisjoint(va_groups)  # group-disjoint (>=2 groups)
    assert len(tr) > 0 and len(va) > 0


def test_single_group_falls_back_to_random(tmp_path):
    rows = train.load_rows(_write_dataset(tmp_path / "ds.jsonl", n=20, groups=("gcd",)))
    X, y, groups = train.build_xy(rows)
    tr, va = train.split(X, y, groups, seed=0)
    assert len(tr) > 0 and len(va) > 0  # 단일 group → random split, 비어있지 않음


def test_train_and_eval_returns_model_and_mae(tmp_path):
    rows = train.load_rows(_write_dataset(tmp_path / "ds.jsonl", n=40))
    X, y, groups = train.build_xy(rows)
    model, mae = train.train_and_eval(X, y, groups, seed=0)
    assert hasattr(model, "predict")
    assert isinstance(mae, float) and mae >= 0.0
    # 재현성 핀: 고정 fixture(n=40, seed=0)의 MAE.
    # sklearn 버전/기본 파라미터 변경 시 갱신. gen-001 winner 승격으로 0.166→0.162985.
    assert mae == pytest.approx(0.16298451, abs=1e-6)


def test_cli_outputs_val_mae_and_saves_model(tmp_path):
    data = _write_dataset(tmp_path / "ds.jsonl", n=40)
    out = tmp_path / "art"
    r = subprocess.run(
        [sys.executable, str(REPO / "train.py"), "--data", str(data),
         "--out", str(out), "--seed", "0"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout.strip().splitlines()[-1])
    assert "val_mae" in payload and isinstance(payload["val_mae"], float)
    assert (out / "model.joblib").exists()
