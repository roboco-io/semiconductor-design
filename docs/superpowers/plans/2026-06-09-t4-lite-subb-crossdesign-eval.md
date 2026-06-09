# T4-lite Sub-B 교차검증 평가 기계 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** held-out 설계(LODO) 교차검증으로 winner의 미관측 설계 일반화를 *방향성 probe*로 측정하는 평가 기계를 `validation.py`에 추가한다(리포트 전용, 자동 promote 무변경).

**Architecture:** `design_fold_splits`(LODO)·`run_crossdesign_gate`(per-design held-out MAE + 방향성 집계)·`render_crossdesign_report`(저표본 caveat) 3개 함수를 `validation.py`에 추가. 기존 `candidate_fold_maes`/`naive_fold_maes` 재사용. 통계 유의성(Wilcoxon/CI) 미산출. `train.py`·`prepare.py`·`dataset` frozen 무변경.

**Tech Stack:** Python 3.12, 기존 `pipeline.validation` 함수, pytest/ruff. 신규 의존성 없음.

**Spec:** `docs/superpowers/specs/2026-06-09-t4-lite-subb-crossdesign-eval-design.md`

**재사용 계약(확인됨):**
- `candidate_fold_maes(train_py, rows, splits, workdir) -> list[float]` — fold별 val MAE(실패 fold=inf). splits=`[(train_idx, val_idx), ...]`.
- `naive_fold_maes(rows, splits) -> list[float]`.
- `run_candidate`/`score_holdout`는 candidate_fold_maes 내부에서 이미 호출(nested resampling).

---

### Task 1: `design_fold_splits` (LODO)

**Files:** Modify `src/pipeline/validation.py` · Test `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_validation.py` 끝에 추가

```python
import pytest
from pipeline.validation import design_fold_splits


def test_design_fold_splits_lodo():
    groups = ["A", "A", "B", "C", "B"]  # 설계 3개
    splits = design_fold_splits(groups)
    assert len(splits) == 3  # 설계당 1 fold
    # 정렬-안정 순서: A, B, C
    tr0, va0 = splits[0]
    assert sorted(va0) == [0, 1]            # A 행
    assert sorted(tr0) == [2, 3, 4]         # 나머지
    for tr, va in splits:
        assert set(tr).isdisjoint(va)
        assert sorted(tr + va) == [0, 1, 2, 3, 4]


def test_design_fold_splits_single_design_raises():
    with pytest.raises(ValueError):
        design_fold_splits(["A", "A", "A"])
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k design_fold_splits -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 추가

```python
def design_fold_splits(groups):
    """Leave-One-Design-Out: 설계(group)마다 1 fold = (train=나머지 설계, val=그 설계).

    교차설계 일반화엔 ≥2 설계 필요(단일 설계면 ValueError). 설계 순서는 sorted-unique로 결정적.
    """
    uniq = sorted(set(groups))
    if len(uniq) < 2:
        raise ValueError(f"교차설계엔 ≥2 설계 필요 (받음: {len(uniq)})")
    splits = []
    for d in uniq:
        va = [i for i, g in enumerate(groups) if g == d]
        tr = [i for i, g in enumerate(groups) if g != d]
        splits.append((tr, va))
    return splits
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k design_fold_splits -v`
Expected: 2 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): design_fold_splits — LODO 교차설계 fold (T4-lite Sub-B)"
```

---

### Task 2: `run_crossdesign_gate` (방향성 집계)

**Files:** Modify `src/pipeline/validation.py` · Test `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — 끝에 추가 (기존 `REPO`·`_rows` 헬퍼 재사용; 3-설계 합성 데이터)

```python
from pipeline.validation import run_crossdesign_gate


def _multidesign_rows(n_per=14):
    rows = []
    for d in ("A", "B", "C"):
        for i in range(n_per):
            rows.append({
                "endpoint": f"{d}e{i}", "startpoint": f"{d}s{i}", "num_stages": 2 + i % 5,
                "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
                "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
                "startpoint_is_ff": i % 2, "endpoint_is_ff": 1, "path_group": "core_clock",
                "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": d,
            })
    return rows


def test_crossdesign_gate_winner_equals_baseline(tmp_path):
    rows = _multidesign_rows()
    res = run_crossdesign_gate(REPO / "train.py", REPO / "train.py", rows, tmp_path / "cd")
    assert res["n_designs"] == 3
    assert res["single_design"] is False
    assert len(res["per_design"]) == 3
    assert abs(res["mean_gap"]) < 0.05          # 동일 모델 → 격차≈0
    assert res["verdict"] in ("mixed", "generalizes_better", "worse")


def test_crossdesign_gate_broken_winner_unverifiable(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    res = run_crossdesign_gate(broken, REPO / "train.py", _multidesign_rows(), tmp_path / "cd2")
    assert res["verdict"] == "unverifiable"
    assert res["n_winner_better"] == 0
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k crossdesign_gate -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 추가

```python
def run_crossdesign_gate(winner_train_py, baseline_train_py, rows, workdir, *, naive=True):
    """held-out 설계(LODO) 교차검증 — 방향성 probe(통계 유의성 미산출, D2).

    설계별(=fold별) held-out MAE를 winner/baseline/naive로 재고, winner가 baseline보다 낮은 설계
    수(n_winner_better)와 평균 격차(mean_gap)로 일반화 *경향*을 보고한다. 소수 설계라 verdict는
    유의성이 아니라 방향성. 실패(inf) 설계는 "검증불가"로 집계 제외.
    """
    workdir = Path(workdir)
    groups = [r["group_key"] for r in rows]
    splits = design_fold_splits(groups)
    uniq = sorted(set(groups))
    w = candidate_fold_maes(winner_train_py, rows, splits, workdir / "winner")
    b = candidate_fold_maes(baseline_train_py, rows, splits, workdir / "baseline")
    nv = naive_fold_maes(rows, splits) if naive else [float("inf")] * len(splits)

    per_design, diffs = [], []
    for d, wm, bm, nm in zip(uniq, w, b, nv):
        valid = wm != float("inf") and bm != float("inf")
        per_design.append({"design": d, "winner_mae": wm, "baseline_mae": bm,
                           "naive_mae": nm, "valid": valid})
        if valid:
            diffs.append(wm - bm)

    n_valid = len(diffs)
    n_winner_better = sum(1 for x in diffs if x < 0)
    mean_gap = float(sum(diffs) / n_valid) if n_valid else float("inf")
    if n_valid == 0:
        verdict = "unverifiable"
    elif n_winner_better > n_valid / 2:
        verdict = "generalizes_better"
    elif n_winner_better < n_valid / 2:
        verdict = "worse"
    else:
        verdict = "mixed"

    return {
        "single_design": False, "n_designs": len(uniq), "n_valid": n_valid,
        "n_winner_better": n_winner_better, "mean_gap": mean_gap,
        "per_design": per_design, "verdict": verdict,
    }
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k crossdesign_gate -v`
Expected: 2 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): run_crossdesign_gate — LODO 방향성 probe(통계 미산출)"
```

---

### Task 3: `render_crossdesign_report` (저표본 caveat)

**Files:** Modify `src/pipeline/validation.py` · Test `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — 끝에 추가

```python
from pipeline.validation import render_crossdesign_report


def test_render_crossdesign_report():
    res = {
        "single_design": False, "n_designs": 3, "n_valid": 3,
        "n_winner_better": 2, "mean_gap": -0.03,
        "per_design": [
            {"design": "A", "winner_mae": 0.10, "baseline_mae": 0.13, "naive_mae": 1.4, "valid": True},
            {"design": "B", "winner_mae": 0.12, "baseline_mae": 0.11, "naive_mae": 1.3, "valid": True},
            {"design": "C", "winner_mae": 0.09, "baseline_mae": 0.15, "naive_mae": 1.5, "valid": True},
        ],
        "verdict": "generalizes_better",
    }
    md = render_crossdesign_report(res)
    assert "generalizes_better" in md
    assert "A" in md and "B" in md and "C" in md       # 설계별 행
    assert "2/3" in md or "2 / 3" in md                 # n_winner_better/n_designs
    assert "probe" in md                                # 방향성 probe 명시
    assert "통계" in md and ("검정 불가" in md or "유의성" in md)  # 저표본 caveat
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k render_crossdesign -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 추가

```python
def render_crossdesign_report(res: dict) -> str:
    """교차설계 일반화 probe 리포트(리포트 전용 — 자동 promote 미편입)."""
    L = ["# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)", ""]
    L.append(f"**verdict: {res['verdict']}**  ·  winner 우세 설계: "
             f"{res['n_winner_better']}/{res['n_designs']}  ·  평균 격차(winner−baseline): "
             f"{res['mean_gap']:+.4f}")
    L.append("")
    L.append("| 설계(held-out) | naive | baseline | winner | 검증 |")
    L.append("|---|---|---|---|---|")
    for p in res["per_design"]:
        ok = "✅" if p["valid"] else "❌검증불가"
        L.append(f"| {p['design']} | {p['naive_mae']:.4f} | {p['baseline_mae']:.4f} | "
                 f"{p['winner_mae']:.4f} | {ok} |")
    L.append("")
    L.append(f"> ⚠️ **저표본**: 설계 {res['n_designs']}개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지")
    L.append("> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을")
    L.append("> 포함한 nested resampling(within-design 게이트와 동일 한계).")
    return "\n".join(L)
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k render_crossdesign -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): render_crossdesign_report + 저표본 probe caveat"
```

---

### Task 4: 전체 회귀 + ruff

- [ ] **Step 1: 전체 테스트**

Run: `uv run pytest -q`
Expected: 모든 테스트 PASS (기존 73 + 신규 ~6).

- [ ] **Step 2: ruff**

Run: `make lint && make fmt`
Expected: 통과. `make fmt`가 frozen(train.py/prepare.py/src/prepare_lib) 재포맷 시 `git restore` 후 in-scope만 커밋.

- [ ] **Step 3: 정리 커밋(있으면)**

```bash
git add src/pipeline tests/pipeline && git commit -m "chore: ruff format crossdesign 모듈" || echo "nothing to format"
```

---

## Self-Review

- **Spec coverage**: D1 LODO(Task1 design_fold_splits) · D2 방향성 probe·통계 미산출(Task2 — Wilcoxon/CI 없음) · D3 신규 함수(Task2 run_crossdesign_gate, 기존 게이트 불변) · D4 리포트 전용(promote 무변경 — 본 plan은 orchestrator 미수정) · D5 합성 fixture(Task2/3 _multidesign_rows) · D6 기계+리포트+테스트(Task1~3). §6 테스트 전부 매핑. ✓
- **Placeholder scan**: 없음 — 전 step 실제 코드. ✓
- **Type consistency**: `design_fold_splits(groups)->list[(list,list)]`, `run_crossdesign_gate(...)->dict(per_design/verdict/n_winner_better/mean_gap/single_design=False)`, `render_crossdesign_report(res)->str`. candidate_fold_maes/naive_fold_maes 기존 시그니처 일치. ✓
- **frozen 주의**: validation만 추가; orchestrator·train.py·prepare.py 무변경(D4 리포트 전용). Task4 ruff가 frozen 건드리면 restore. ✓
- **verdict 임계**: n_winner_better > n_valid/2 → generalizes_better, < → worse, == → mixed, n_valid=0 → unverifiable. inf 설계 제외. 명확. ✓
