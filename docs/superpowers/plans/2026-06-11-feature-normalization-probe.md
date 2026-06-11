# Feature 정규화 probe 구현 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 정규화 변형 3개(V1 델타 label · V2 설계별 상대화 · V3 무차원 비율)를 gcd+aes LODO 2-fold로 실측해, "어느 축이 교차설계 전이를 살리는가"를 naive 기준(사전 고정)으로 판정한다.

**Architecture:** 변형 = 현 winner `train.py`의 전체 사본에서 정규화 부분만 수정(계약 유지 → 기존 `candidate_fold_maes`/`score_holdout` 무수정 재사용). 드라이버 `run_probe.py`가 변형 3 + 대조군 2(winner·baseline) + naive를 LODO로 평가해 `probe.md` 생성. 전부 `experiments/multidesign/probe/` Operator-owned 일회성, frozen 무변경.

**Tech Stack:** Python 3.12 (uv), sklearn+numpy(변형 내부), pytest, 기존 `src/pipeline/validation.py` 채점기.

**Spec:** `docs/superpowers/specs/2026-06-11-feature-normalization-probe-design.md`

**공통 규칙 (모든 task):**
- frozen 파일(`train.py`, `prepare.py`, `src/prepare_lib/`, 기존 dataset) 절대 수정 금지. `make fmt`가 frozen을 재포맷하면 `git restore`로 복원하고 in-scope 파일만 커밋.
- 커밋 전 `uv run pytest -q` green 필수. ruff line-length 100.
- pytest는 `pythonpath = ["src", "."]`라 `from pipeline.validation import ...`가 바로 된다.

---

## File 구조

| 파일 | 책임 |
|---|---|
| `experiments/multidesign/probe/run_probe.py` | 판정 함수 + 리포트 렌더 + LODO 드라이버 + CLI |
| `experiments/multidesign/probe/v1_delta.py` | train.py 사본 — label을 델타(post_route−synth)로 |
| `experiments/multidesign/probe/v2_groupstat.py` | train.py 사본 — 수치 feature 설계별 표준화 |
| `experiments/multidesign/probe/v3_ratio.py` | train.py 사본 — 절대 ns feature → 무차원 비율 |
| `tests/probe/conftest.py` | probe 모듈 로더(importlib) + 2설계 합성 fixture |
| `tests/probe/test_probe_verdict.py` | 판정 규칙 4경로 + 동률 경계 + 리포트 렌더 |
| `tests/probe/test_variants.py` | 변형 3개 계약 스모크(candidate_fold_maes 왕복) |
| `tests/probe/test_run_probe_driver.py` | 드라이버 end-to-end(변형 1개로 runtime 제한) |

---

### Task 1: 판정 함수 + 리포트 렌더 (`run_probe.py` 1차)

**Files:**
- Create: `tests/probe/conftest.py`
- Create: `tests/probe/test_probe_verdict.py`
- Create: `experiments/multidesign/probe/run_probe.py`

- [ ] **Step 1: conftest 작성**

```python
# tests/probe/conftest.py
"""probe 테스트 공용 — experiments/multidesign/probe 모듈 로더 + 2설계 합성 fixture."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "experiments" / "multidesign" / "probe"


def load_probe_module(name: str):
    spec = importlib.util.spec_from_file_location(name, PROBE_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def run_probe_mod():
    return load_probe_module("run_probe")


@pytest.fixture(scope="session")
def probe_dir():
    return PROBE_DIR


@pytest.fixture
def probe_rows():
    # 2설계, label 오프셋 정반대(실데이터 gcd 음수/aes 양수 모사). post_route는 학습 가능한
    # 관계(synth − 0.02×stages)로 생성 — 변형이 finite MAE를 내는지 보는 스모크용.
    rows = []
    for d, offset in (("alpha", -1.0), ("beta", 1.5)):
        for i in range(24):
            stages = 2 + i % 5
            synth_slack = offset + 0.05 * (i % 8)
            rows.append(
                {
                    "endpoint": f"{d}/e{i}",
                    "startpoint": f"{d}/s{i}",
                    "num_stages": stages,
                    "synth_slack_ns": synth_slack,
                    "synth_arrival_ns": 0.5 + 0.03 * (i % 6),
                    "max_stage_delay_ns": 0.1 + 0.015 * (i % 3),
                    "mean_stage_delay_ns": 0.05 + 0.005 * (i % 3),
                    "startpoint_is_ff": i % 2,
                    "endpoint_is_ff": (i + 1) % 2,
                    "path_group": "core_clock" if i % 2 else "io",
                    "post_route_slack_ns": synth_slack - 0.02 * stages,
                    "group_key": d,
                }
            )
    return rows
```

- [ ] **Step 2: 실패하는 테스트 작성**

```python
# tests/probe/test_probe_verdict.py
"""판정 규칙(naive 기준 사전 고정, spec §5) + 리포트 렌더."""

INF = float("inf")


def test_transferable_when_below_naive_on_all_designs(run_probe_mod):
    assert run_probe_mod.probe_verdict([1.0, 1.0], [1.5, 1.4]) == "transferable"


def test_partial_when_below_naive_on_one_design(run_probe_mod):
    assert run_probe_mod.probe_verdict([1.0, 2.0], [1.5, 1.4]) == "partial"


def test_not_transferable_when_above_naive(run_probe_mod):
    assert run_probe_mod.probe_verdict([2.0, 2.0], [1.5, 1.4]) == "not_transferable"


def test_tie_counts_as_not_below(run_probe_mod):
    # 동률은 naive 이상으로 취급(사전 고정 규칙 — 결과 보고 기준 이동 금지).
    assert run_probe_mod.probe_verdict([1.5, 1.4], [1.5, 1.4]) == "not_transferable"


def test_unverifiable_on_any_inf(run_probe_mod):
    assert run_probe_mod.probe_verdict([INF, 1.0], [1.5, 1.4]) == "unverifiable"


def test_render_report_has_naive_verdicts_and_caveat(run_probe_mod):
    res = {
        "designs": ["aes", "gcd"],
        "naive": [1.7198, 1.4117],
        "results": {"winner": [2.74, 2.51], "v1_delta": [1.2, 1.1]},
        "verdicts": {"v1_delta": "transferable"},
    }
    md = run_probe_mod.render_probe_report(res)
    assert "naive" in md
    assert "v1_delta" in md and "transferable" in md
    assert "winner" in md  # 대조군은 verdict 없이 수치만
    assert "2 fold" in md or "2-fold" in md  # 저표본 caveat 명기
```

- [ ] **Step 3: 실패 확인**

Run: `uv run pytest tests/probe/test_probe_verdict.py -q`
Expected: FAIL — `FileNotFoundError`(run_probe.py 미존재) 또는 AttributeError.

- [ ] **Step 4: run_probe.py 1차 구현 (판정+렌더만, 드라이버는 Task 5)**

```python
# experiments/multidesign/probe/run_probe.py
"""feature 정규화 probe 드라이버 — LODO 2-fold, naive 기준 사전 고정 판정.

Operator-owned 일회성 실험(루프 후보 아님). frozen 무변경 — 변형은 train.py 사본.
spec: docs/superpowers/specs/2026-06-11-feature-normalization-probe-design.md
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from pipeline.validation import (  # noqa: E402
    candidate_fold_maes,
    design_fold_splits,
    naive_fold_maes,
)

_TIE_EPS = 1e-9  # 부동소수 잔차가 win으로 새지 않게 (validation.py 패턴)
CONTROLS = ("winner", "baseline")  # 대조군 — verdict 미산출(이미 crossdesign.md에서 판정)


def probe_verdict(variant_maes: list[float], naive_maes: list[float]) -> str:
    """spec §5: 두 설계 모두 naive 미만 → transferable. inf 하나라도 → unverifiable."""
    if any(m == float("inf") for m in variant_maes):
        return "unverifiable"
    wins = sum(1 for v, n in zip(variant_maes, naive_maes) if v < n - _TIE_EPS)
    if wins == len(naive_maes):
        return "transferable"
    if wins >= 1:
        return "partial"
    return "not_transferable"


def _fmt(m: float) -> str:
    return "inf" if m == float("inf") else f"{m:.4f}"


def render_probe_report(res: dict) -> str:
    designs = res["designs"]
    L = ["# Feature 정규화 probe 리포트 (LODO · naive 기준 사전 고정)", ""]
    L.append("| 스크립트 | " + " | ".join(f"{d} (held-out)" for d in designs) + " | verdict |")
    L.append("|---" * (len(designs) + 2) + "|")
    L.append("| naive | " + " | ".join(_fmt(m) for m in res["naive"]) + " | (기준) |")
    for name, maes in res["results"].items():
        v = res["verdicts"].get(name, "—")
        L.append(f"| {name} | " + " | ".join(_fmt(m) for m in maes) + f" | {v} |")
    L.append("")
    L.append(
        f"> ⚠️ 설계 {len(designs)}개 → {len(designs)} fold 저표본 — 방향성 probe(통계 검정 불가)."
    )
    L.append("> 판정 규칙은 결과 확인 전 spec §5에 고정됨(post-hoc 기준 이동 금지, gen-002 교훈).")
    return "\n".join(L)
```

(드라이버 `run_probe()`/`main()`은 Task 5에서 추가 — 이 시점엔 위까지만.)

- [ ] **Step 5: 통과 확인**

Run: `uv run pytest tests/probe/test_probe_verdict.py -q`
Expected: 6 passed

- [ ] **Step 6: 커밋**

```bash
git add tests/probe/conftest.py tests/probe/test_probe_verdict.py experiments/multidesign/probe/run_probe.py
git commit -m "feat(probe): 판정 규칙(naive 기준 사전 고정) + 리포트 렌더 (정규화 probe Task 1)"
```

---

### Task 2: V1 — 델타 label 변형

**Files:**
- Create: `experiments/multidesign/probe/v1_delta.py` (train.py 사본 + 2개 편집)
- Create: `tests/probe/test_variants.py`

- [ ] **Step 1: 실패하는 스모크 테스트 작성**

```python
# tests/probe/test_variants.py
"""변형 3개 계약 스모크 — candidate_fold_maes 왕복(학습→model.joblib→score_holdout)."""

import math

from pipeline.validation import candidate_fold_maes, design_fold_splits


def _smoke(script, probe_rows, tmp_path):
    splits = design_fold_splits([r["group_key"] for r in probe_rows])
    maes = candidate_fold_maes(script, probe_rows, splits[:1], tmp_path)
    assert len(maes) == 1
    assert math.isfinite(maes[0])  # inf면 계약 위반(학습 실패/모델 미저장/채점 실패)


def test_v1_delta_contract_roundtrip(probe_dir, probe_rows, tmp_path):
    _smoke(probe_dir / "v1_delta.py", probe_rows, tmp_path)
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/probe/test_variants.py -q`
Expected: FAIL — v1_delta.py 미존재(candidate_fold_maes가 inf 반환 → assert 실패).

- [ ] **Step 3: 사본 생성 + 편집**

```bash
cp train.py experiments/multidesign/probe/v1_delta.py
```

v1_delta.py에서 docstring 첫 줄 교체:

```python
# old
"""train.py — surrogate 모델 학습 (에이전트가 변형하는 단일 파일, self-contained).
# new
"""v1_delta.py — probe 변형 V1: 델타 label(잔차 학습). train.py 사본, Operator-owned.
```

`build_xy`의 y 정의 교체:

```python
# old
    X = np.asarray(feats, dtype=float)
    y = np.asarray([float(r[LABEL]) for r in rows], dtype=float)
# new
    X = np.asarray(feats, dtype=float)
    # V1: label을 델타(post_route − synth)로 — 설계 간 오프셋을 label에서 제거.
    # MAE 동일성: |Δ̂−Δ| = |(synth+Δ̂)−post_route| 이므로 절대 slack MAE와 그대로 비교 가능.
    y = np.asarray(
        [float(r[LABEL]) - float(r["synth_slack_ns"]) for r in rows], dtype=float
    )
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/probe/test_variants.py -q`
Expected: 1 passed (수십 초 — 실제 sklearn 학습 1 fold)

- [ ] **Step 5: 커밋**

```bash
git add experiments/multidesign/probe/v1_delta.py tests/probe/test_variants.py
git commit -m "feat(probe): V1 델타 label 변형 — 설계 간 label 오프셋 제거 (Task 2)"
```

---

### Task 3: V2 — 설계별 통계 상대화 변형

**Files:**
- Create: `experiments/multidesign/probe/v2_groupstat.py` (train.py 사본 + 2개 편집)
- Modify: `tests/probe/test_variants.py` (테스트 1개 추가)

- [ ] **Step 1: 실패하는 테스트 추가** (test_variants.py 끝에)

```python
def test_v2_groupstat_contract_roundtrip(probe_dir, probe_rows, tmp_path):
    _smoke(probe_dir / "v2_groupstat.py", probe_rows, tmp_path)
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/probe/test_variants.py::test_v2_groupstat_contract_roundtrip -q`
Expected: FAIL

- [ ] **Step 3: 사본 생성 + 편집**

```bash
cp train.py experiments/multidesign/probe/v2_groupstat.py
```

docstring 첫 줄 교체:

```python
# old
"""train.py — surrogate 모델 학습 (에이전트가 변형하는 단일 파일, self-contained).
# new
"""v2_groupstat.py — probe 변형 V2: 설계별 synth 통계 표준화. train.py 사본, Operator-owned.
```

`build_xy` 끝부분 교체:

```python
# old
    X = np.asarray(feats, dtype=float)
    y = np.asarray([float(r[LABEL]) for r in rows], dtype=float)
    groups = [r[GROUP] for r in rows]
    return X, y, groups
# new
    X = np.asarray(feats, dtype=float)
    y = np.asarray([float(r[LABEL]) for r in rows], dtype=float)
    groups = [r[GROUP] for r in rows]
    # V2: 수치 열(0~4)을 그 행의 설계별 통계로 표준화. label·이진(5,6)·pg 코드(7)는 유지.
    # held-out 설계도 자기 synth 통계를 쓴다 — synth는 추론 시점 가용 정보라 누수 아님.
    eps = 1e-9
    garr = np.asarray(groups)
    for g in np.unique(garr):
        m = garr == g
        for c in range(5):
            X[m, c] = (X[m, c] - X[m, c].mean()) / (X[m, c].std() + eps)
    return X, y, groups
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/probe/test_variants.py -q`
Expected: 2 passed

- [ ] **Step 5: 커밋**

```bash
git add experiments/multidesign/probe/v2_groupstat.py tests/probe/test_variants.py
git commit -m "feat(probe): V2 설계별 통계 상대화 변형 — feature 스케일 정렬 (Task 3)"
```

---

### Task 4: V3 — 무차원 비율 feature 변형

**Files:**
- Create: `experiments/multidesign/probe/v3_ratio.py` (train.py 사본 + 3개 편집)
- Modify: `tests/probe/test_variants.py` (테스트 1개 추가)

- [ ] **Step 1: 실패하는 테스트 추가**

```python
def test_v3_ratio_contract_roundtrip(probe_dir, probe_rows, tmp_path):
    _smoke(probe_dir / "v3_ratio.py", probe_rows, tmp_path)
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/probe/test_variants.py::test_v3_ratio_contract_roundtrip -q`
Expected: FAIL

- [ ] **Step 3: 사본 생성 + 편집**

```bash
cp train.py experiments/multidesign/probe/v3_ratio.py
```

docstring 첫 줄 교체:

```python
# old
"""train.py — surrogate 모델 학습 (에이전트가 변형하는 단일 파일, self-contained).
# new
"""v3_ratio.py — probe 변형 V3: 무차원 비율 feature(스케일 제거). train.py 사본, Operator-owned.
```

`build_xy`의 feats 블록 교체 (절대 ns 4열 → 무차원 비율 3열, 총 7 feature — spec §3):

```python
# old
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
# new
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
```

`add_timing_features` 전체 교체 (8열 전제 → 7열 무차원 전제; 기존 함수 `def add_timing_features`부터 `return np.hstack([X, extra])`까지 전부를 아래로):

```python
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
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/probe/test_variants.py -q`
Expected: 3 passed

- [ ] **Step 5: 커밋**

```bash
git add experiments/multidesign/probe/v3_ratio.py tests/probe/test_variants.py
git commit -m "feat(probe): V3 무차원 비율 feature 변형 — 절대 ns 스케일 제거 (Task 4)"
```

---

### Task 5: 드라이버 완성 (`run_probe()` + CLI)

**Files:**
- Modify: `experiments/multidesign/probe/run_probe.py` (Task 1 파일 끝에 추가)
- Create: `tests/probe/test_run_probe_driver.py`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/probe/test_run_probe_driver.py
"""드라이버 end-to-end — runtime 제한 위해 변형 1개(v1)만으로 LODO 2 fold."""

import math


def test_run_probe_end_to_end_v1_only(run_probe_mod, probe_dir, probe_rows):
    res = run_probe_mod.run_probe(probe_rows, {"v1_delta": probe_dir / "v1_delta.py"})
    assert res["designs"] == ["alpha", "beta"]
    assert len(res["naive"]) == 2
    assert set(res["results"]) == {"v1_delta"}
    assert all(math.isfinite(m) for m in res["results"]["v1_delta"])
    assert res["verdicts"]["v1_delta"] in {
        "transferable", "partial", "not_transferable", "unverifiable",
    }
    md = run_probe_mod.render_probe_report(res)
    assert "v1_delta" in md
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/probe/test_run_probe_driver.py -q`
Expected: FAIL — `AttributeError: module 'run_probe' has no attribute 'run_probe'`

- [ ] **Step 3: 드라이버 구현** (run_probe.py 끝에 추가)

먼저 파일 상단 import에 두 줄 추가 (Task 1에선 미사용이라 뺐던 것):

```python
import tempfile   # import sys 아래에
import click      # from pathlib import Path 아래 빈 줄 다음에
```

그 다음 파일 끝에 추가:

```python
def run_probe(rows: list[dict], scripts: dict[str, Path]) -> dict:
    """scripts(이름→train.py 계약 스크립트)를 LODO로 평가. fold 작업물은 tempdir(126M 교훈)."""
    groups = [r["group_key"] for r in rows]
    splits = design_fold_splits(groups)
    designs = sorted(set(groups))
    naive = naive_fold_maes(rows, splits)
    results = {}
    for name, script in scripts.items():
        with tempfile.TemporaryDirectory(prefix=f"probe-{name}-") as wd:
            results[name] = candidate_fold_maes(Path(script), rows, splits, Path(wd))
    verdicts = {
        name: probe_verdict(results[name], naive) for name in results if name not in CONTROLS
    }
    return {"designs": designs, "naive": naive, "results": results, "verdicts": verdicts}


@click.command()
@click.option("--dataset", default=str(HERE.parent / "dataset.jsonl"), type=click.Path(exists=True))
@click.option("--baseline", required=True, type=click.Path(exists=True),
              help="pre-gen-001 train.py (git show 619e24f~1:train.py 로 추출)")
@click.option("--out", default=str(HERE / "probe.md"), type=click.Path())
def main(dataset: str, baseline: str, out: str) -> None:
    import json

    rows = [
        json.loads(line)
        for line in Path(dataset).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    scripts = {
        "winner": ROOT / "train.py",
        "baseline": Path(baseline),
        "v1_delta": HERE / "v1_delta.py",
        "v2_groupstat": HERE / "v2_groupstat.py",
        "v3_ratio": HERE / "v3_ratio.py",
    }
    res = run_probe(rows, scripts)
    Path(out).write_text(render_probe_report(res) + "\n", encoding="utf-8")
    click.echo(render_probe_report(res))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 통과 확인 (전체 회귀 포함)**

Run: `uv run pytest tests/probe -q && uv run pytest -q`
Expected: probe 테스트 전체 + 기존 83개 전부 passed

- [ ] **Step 5: 커밋**

```bash
git add experiments/multidesign/probe/run_probe.py tests/probe/test_run_probe_driver.py
git commit -m "feat(probe): LODO 드라이버 + CLI — 변형/대조군 일괄 평가, tempdir 격리 (Task 5)"
```

---

### Task 6: 실측 실행 → probe.md (Operator 단계)

**Files:**
- Create: `experiments/multidesign/probe/probe.md` (실행 산출물)

- [ ] **Step 1: baseline 추출 + 실행** (로컬 CPU, 수 분)

```bash
git show 619e24f~1:train.py > /tmp/pre_gen001_train.py
uv run python experiments/multidesign/probe/run_probe.py --baseline /tmp/pre_gen001_train.py
```

Expected: stdout에 리포트 표(naive 행 = aes 1.7198 / gcd 1.4117과 일치해야 정상 — 2026-06-10 실측 재현), `experiments/multidesign/probe/probe.md` 생성.

- [ ] **Step 2: sanity 확인**

winner/baseline 행이 crossdesign.md(2026-06-10)와 일치하는지 비교: winner aes 2.7393/gcd 2.5122, baseline aes 3.0486/gcd 2.4424. 불일치면 **정지·원인 조사**(결정성 위반 신호).

- [ ] **Step 3: 커밋**

```bash
git add experiments/multidesign/probe/probe.md
git commit -m "experiment(probe): 정규화 변형 LODO 실측 — V1/V2/V3 naive 기준 판정"
```

---

### Task 7: INTENT Learnings 기록 + push (Operator 단계)

**Files:**
- Modify: `INTENT.md` (Learnings 최상단)

- [ ] **Step 1: Learnings 항목 작성** — 다음 골격에 실측 수치·verdict를 채워 기록:

```markdown
- **2026-06-11** (정규화 probe — 어느 축이 교차설계 전이를 살리는가) — V1(델타 label) [verdict],
  V2(설계별 상대화) [verdict], V3(무차원 비율) [verdict] (naive 기준 사전 고정, LODO 2-fold).
  [핵심 해석 2~3문장: 어느 축이 효과/무효였고 그 의미]. ibex 결정: [probe 결과에 따른 방향].
  리포트: [probe.md](experiments/multidesign/probe/probe.md).
```

- [ ] **Step 2: 최종 검증 + push**

```bash
uv run pytest -q   # green 확인
git add INTENT.md && git commit -m "docs(intent): Learnings 2026-06-11 — 정규화 probe 실측 결과"
git push && git status -sb   # push 성공 확인
```

- [ ] **Step 3: Operator 보고** — probe.md 표 + verdict + ibex 진행/보류 권고(spec §5 후속 행동 매핑)를 사용자에게 보고. ibex run-task는 별도 비용 동의 없이는 진행 금지.
