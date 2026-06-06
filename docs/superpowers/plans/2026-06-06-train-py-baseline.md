# train.py Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build the baseline `train.py` — a self-contained, agent-mutable single file that reads prepare.py's `dataset.jsonl`, trains a scikit-learn `HistGradientBoostingRegressor` to predict per-endpoint `post_route_slack_ns`, prints `{"val_mae": <float>}`, and saves `model.joblib`.

**Architecture:** `train.py` is the karpathy-style single file the AutoResearch agent mutates — therefore SELF-CONTAINED (stdlib + sklearn only, NO `prepare_lib` import). A minimal fixed contract (input `--data`, output `{"val_mae"}` JSON + `model.joblib`) is all the loop depends on; everything else is freely mutable. Tested fixture-first against a synthetic dataset.

**Tech Stack:** Python 3.12, uv, scikit-learn (HistGradientBoostingRegressor, GroupShuffleSplit, mean_absolute_error), numpy (transitive), joblib (transitive via sklearn), click, stdlib json. ruff 100char/py312.

**Spec:** `docs/superpowers/specs/2026-06-06-od4-train-baseline-design.md`. **Frozen input:** prepare.py row schema — 8 features + `post_route_slack_ns` + `group_key`. OD-1/OD-4 fixed.

---

## Files

| File | Change |
|---|---|
| `pyproject.toml` | add `ml` optional-dep `scikit-learn>=1.4`. |
| `train.py` | replace NotImplementedError skeleton with self-contained baseline. |
| `Makefile` | add `train` target. |
| `tests/train/test_train.py` | unit (build_xy, split, train_and_eval) + subprocess contract test. |

**Self-contained rule:** `train.py` must NOT import `prepare_lib` or any project module. It re-declares its expected feature list locally (it consumes the frozen `dataset.jsonl`, not the parser). This keeps the agent's mutation surface one file.

**Contract (fixed):**
```
input  : --data <dataset.jsonl>  (rows: 8 features + post_route_slack_ns + group_key)
output : stdout single line {"val_mae": <float>}
artifact: --out <dir>/model.joblib
```

---

### Task 1: Add scikit-learn dependency

**Files:** Modify `pyproject.toml`

- [ ] **Step 1: Add the `ml` optional-dependency**

In `pyproject.toml`, under `[project.optional-dependencies]`, after the `pipeline = [...]` block, add:

```toml
ml = [
    "scikit-learn>=1.4",
]
```

- [ ] **Step 2: Sync and verify import**

Run: `uv sync --all-extras && uv run python -c "import sklearn, numpy, joblib; print(sklearn.__version__)"`
Expected: prints a sklearn version (e.g. `1.x.y`), no ImportError.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: scikit-learn ml 의존성 추가 (OD-4 baseline)"
```

---

### Task 2: `train.py` data loading + feature matrix

**Files:**
- Modify: `train.py` (replace skeleton)
- Test: `tests/train/test_train.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/train/test_train.py
import json
from pathlib import Path

import train


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/train/test_train.py -v`
Expected: FAIL — `train.load_rows` does not exist (skeleton raises NotImplementedError on import).

- [ ] **Step 3: Begin `train.py` (replace skeleton) with load + build_xy**

```python
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
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit, train_test_split

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
    text = Path(data_path).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def build_xy(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    # path_group(문자열)을 정렬-안정 ordinal 코드로 인코딩.
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
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/train/test_train.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add train.py tests/train/test_train.py
git commit -m "feat(train): dataset.jsonl 로드 + feature 행렬 (self-contained)"
```

---

### Task 3: split + train_and_eval

**Files:**
- Modify: `train.py`
- Modify: `tests/train/test_train.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/train/test_train.py
import numpy as np


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/train/test_train.py -k "split or train_and_eval" -v`
Expected: FAIL — `train.split` / `train.train_and_eval` undefined.

- [ ] **Step 3: Append to `train.py`**

```python
def split(X, y, groups, seed: int = 0):
    # group(=design_id) ≥2면 group-disjoint, 단일 group이면 fixed-seed random.
    if len(set(groups)) >= 2:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
        tr, va = next(gss.split(X, y, groups=groups))
        return tr, va
    idx = np.arange(len(y))
    tr, va = train_test_split(idx, test_size=0.25, random_state=seed)
    return tr, va


def train_and_eval(X, y, groups, seed: int = 0) -> tuple[object, float]:
    tr, va = split(X, y, groups, seed=seed)
    model = HistGradientBoostingRegressor(random_state=seed)
    model.fit(X[tr], y[tr])
    pred = model.predict(X[va])
    mae = float(mean_absolute_error(y[va], pred))
    return model, mae
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/train/test_train.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add train.py tests/train/test_train.py
git commit -m "feat(train): group-disjoint split + HistGBDT fit + val MAE"
```

---

### Task 4: CLI contract (`--data`/`--out` → JSON + model.joblib)

**Files:**
- Modify: `train.py`
- Modify: `Makefile`
- Modify: `tests/train/test_train.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/train/test_train.py
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]


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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/train/test_train.py::test_cli_outputs_val_mae_and_saves_model -v`
Expected: FAIL — `train.py` has no CLI / `main`.

- [ ] **Step 3: Append the CLI to `train.py`**

```python
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
```

- [ ] **Step 4: Add Makefile `train` target**

Add `train` to the `.PHONY` line and append after the `prepare:` block:

```makefile
train:
	uv run python train.py --data $(DATA) --out $(OUT) --seed $(SEED)
```

- [ ] **Step 5: Run to verify it passes + full suite + lint**

Run: `uv run pytest -q && uv run ruff check src tests prepare.py train.py`
Expected: all PASS, ruff clean.

- [ ] **Step 6: Commit**

```bash
git add train.py Makefile tests/train/test_train.py
git commit -m "feat(train): click CLI {\"val_mae\"} + model.joblib + make train"
```

---

### Task 5: End-to-end smoke (prepare → train) + verify

**Files:** none (verification only)

- [ ] **Step 1: Chain prepare.py → train.py on a synthetic dataset**

The real fixture dataset (2 samples) is too small to train; generate a synthetic dataset and run the real CLI end-to-end:

```bash
cd /Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design
uv run python - <<'PY'
import json, pathlib
rows=[]
for i in range(60):
    g="gcd" if i%2 else "ibex"
    rows.append({"endpoint":f"e{i}","startpoint":f"s{i}","num_stages":2+i%5,
      "synth_slack_ns":0.4-(i%6)*0.1,"synth_arrival_ns":0.3+(i%4)*0.2,
      "max_stage_delay_ns":0.1+(i%3)*0.15,"mean_stage_delay_ns":0.05+(i%3)*0.05,
      "startpoint_is_ff":i%2,"endpoint_is_ff":1,"path_group":"clk" if i%2 else "clk2",
      "post_route_slack_ns":0.5-(i%7)*0.1,"group_key":g})
pathlib.Path("/tmp/train-ds.jsonl").write_text("\n".join(json.dumps(r) for r in rows)+"\n")
print("wrote", len(rows))
PY
make train DATA=/tmp/train-ds.jsonl OUT=/tmp/train-art SEED=0
ls -l /tmp/train-art/model.joblib
```
Expected: prints `{"val_mae": <float>}`, `model.joblib` exists.

- [ ] **Step 2: Confirm full suite + lint green**

Run: `uv run pytest -q && uv run ruff check src tests prepare.py train.py`
Expected: all PASS, ruff clean.

---

## Self-Review

**Spec coverage:** sklearn HistGradientBoostingRegressor baseline (Task 2-3) · contract `--data`→`{"val_mae"}`+`model.joblib` (Task 4) · group-disjoint split w/ single-group fallback (Task 3) · self-contained single file, no prepare_lib import (Task 2 docstring + imports) · fixture-first synthetic dataset (all tasks) · NFR-1 sklearn-only dep (Task 1). val-gaming defense + held-out test = explicitly loop-scope deferred (spec §6), not in this plan.

**Placeholder scan:** none — complete code/fixtures/commands throughout.

**Type consistency:** `FEATURE_NAMES` (8 names) used by `build_xy`; `build_xy → (np.ndarray, np.ndarray, list[str])` consumed by `split`/`train_and_eval`; `train_and_eval → (model, float)` consumed by `main`. `load_rows`/`build_xy`/`split`/`train_and_eval`/`main` names consistent across tasks and tests. `--data`/`--out`/`--seed` CLI options match the subprocess test and Makefile target. No dead code (encoding inlined via `pg_code` in `build_xy`).
