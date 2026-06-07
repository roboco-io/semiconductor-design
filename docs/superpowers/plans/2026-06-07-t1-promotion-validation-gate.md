# T1 승격 검증 게이트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** winner 승격 직전, naive·baseline·winner를 동일 fold(repeated 5-fold×10)에서 paired 비교해 "통계적으로 baseline을 이기나"를 advisory 리포트로 산출하는 검증 게이트를 만든다.

**Architecture:** 신규 `src/pipeline/validation.py` 한 모듈에 fold 분할·후보 fold MAE(기존 `run_candidate`+`score_holdout` 재사용)·naive fold MAE·paired 통계(bootstrap CI + scipy Wilcoxon + Cohen's dz)·verdict·리포트 렌더를 모은다. `operator_gate`는 리포트를 승격 전 표시만 한다. 모두 advisory — Operator가 결정(H-B). train.py·prepare.py·dataset 무변경.

**Tech Stack:** Python 3.12, numpy(bootstrap), scipy.stats.wilcoxon(sklearn 경유 가용), sklearn KFold, 기존 `pipeline.runner.run_candidate`·`pipeline.holdout.score_holdout`. pytest/ruff.

**Spec:** `docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md`

**핵심 재사용 계약(확인됨):**
- `run_candidate(train_py, dataset, out_dir, seed=0) -> float`: train.py를 subprocess 실행, `out_dir/model.joblib` 저장. 실패 시 `float("inf")`.
- `score_holdout(train_py, model_path, holdout_jsonl) -> float`: winner 모듈 로드 + model.joblib로 holdout jsonl 채점(MAE). gen-001 `__main__` pickle 이슈 이미 처리.
- 따라서 한 fold의 paired MAE = `run_candidate(train_py, train_fold.jsonl, out)` 후 `score_holdout(train_py, out/"model.joblib", val_fold.jsonl)`.

---

### Task 1: fold_splits + naive_fold_maes (순수 함수)

**Files:**
- Create: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_validation.py`

```python
# tests/pipeline/test_validation.py
from pipeline.validation import fold_splits, naive_fold_maes


def test_fold_splits_count_and_partition():
    splits = fold_splits(50, k=5, repeats=10, base_seed=0)
    assert len(splits) == 50  # 5 fold × 10 repeat
    tr, va = splits[0]
    assert sorted(tr + va) == list(range(50))  # train+val == 전체
    assert set(tr).isdisjoint(va)  # 겹침 없음
    assert 8 <= len(va) <= 12  # 50/5 ≈ 10


def test_fold_splits_deterministic():
    a = fold_splits(40, k=5, repeats=2, base_seed=7)
    b = fold_splits(40, k=5, repeats=2, base_seed=7)
    assert a == b  # 같은 seed → 같은 split (재현성)


def test_naive_fold_maes_handcomputed():
    rows = [
        {"synth_slack_ns": 0.5, "post_route_slack_ns": 0.2},  # |0.5-0.2|=0.3
        {"synth_slack_ns": 0.0, "post_route_slack_ns": -0.4},  # 0.4
        {"synth_slack_ns": 1.0, "post_route_slack_ns": 1.0},  # 0.0
    ]
    splits = [([0], [1, 2]), ([1], [0, 2])]
    maes = naive_fold_maes(rows, splits)
    assert maes[0] == (0.4 + 0.0) / 2  # val={1,2}
    assert maes[1] == (0.3 + 0.0) / 2  # val={0,2}
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -v`
Expected: FAIL — `ModuleNotFoundError: pipeline.validation`

- [ ] **Step 3: 구현** — `src/pipeline/validation.py` 생성

```python
"""validation — 승격 검증 게이트 (T1). naive·baseline·winner를 동일 fold에서 paired 비교.

advisory only — Operator 승격 결정(H-B)을 통계적 근거로 보조할 뿐 자동 거부하지 않는다.
train.py·prepare.py·dataset 무변경 (읽기 + 임시 fold 분할만).
설계: docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md
"""

from __future__ import annotations

from sklearn.model_selection import KFold


def fold_splits(n: int, k: int = 5, repeats: int = 10, base_seed: int = 0):
    """repeated K-fold split 인덱스 리스트. 각 원소 = (train_idx, val_idx)."""
    splits = []
    for r in range(repeats):
        kf = KFold(n_splits=k, shuffle=True, random_state=base_seed + r)
        for tr, va in kf.split(range(n)):
            splits.append((tr.tolist(), va.tolist()))
    return splits


def naive_fold_maes(rows: list[dict], splits) -> list[float]:
    """naive 예측(합성 슬랙=최종 슬랙)의 fold별 val MAE."""
    maes = []
    for _tr, va in splits:
        errs = [abs(rows[j]["synth_slack_ns"] - rows[j]["post_route_slack_ns"]) for j in va]
        maes.append(sum(errs) / len(errs))
    return maes
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -v`
Expected: 3 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): fold_splits + naive_fold_maes (T1 토대)"
```

---

### Task 2: candidate_fold_maes (train.py 학습 → score_holdout 채점)

**Files:**
- Modify: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_validation.py` 끝에 추가

```python
import json
from pathlib import Path

from pipeline.validation import candidate_fold_maes, fold_splits

REPO = Path(__file__).resolve().parents[2]


def _rows(n=40):
    return [{
        "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
        "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
        "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
        "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
        "path_group": "core_clock",
        "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd",
    } for i in range(n)]


def test_candidate_fold_maes_real_trainpy(tmp_path):
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)  # 5 fold (빠르게)
    maes = candidate_fold_maes(REPO / "train.py", rows, splits, tmp_path / "wd")
    assert len(maes) == 5
    assert all(m >= 0.0 and m != float("inf") for m in maes)


def test_candidate_fold_maes_broken_trainpy_inf(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)
    maes = candidate_fold_maes(broken, rows, splits, tmp_path / "wd2")
    assert all(m == float("inf") for m in maes)  # 모든 fold 실패
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k candidate_fold -v`
Expected: FAIL — `ImportError: cannot import name 'candidate_fold_maes'`

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 import + 함수 추가

상단 import에 추가:
```python
import json
from pathlib import Path

from pipeline.holdout import score_holdout
from pipeline.runner import run_candidate
```

함수 추가:
```python
def _write_jsonl(rows: list[dict], path: Path) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def candidate_fold_maes(train_py, rows: list[dict], splits, workdir: Path) -> list[float]:
    """후보 train.py를 각 fold의 train으로 학습하고, 같은 fold의 val에서 paired MAE를 잰다.

    train.py가 어떤 fold에서 실패하면 그 fold MAE = inf (검증 불가 신호).
    validation이 split을 통제하므로 train.py 내부 split과 무관하게 paired가 성립한다.
    """
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    maes = []
    for i, (tr, va) in enumerate(splits):
        train_path = _write_jsonl([rows[j] for j in tr], workdir / f"f{i}_train.jsonl")
        val_path = _write_jsonl([rows[j] for j in va], workdir / f"f{i}_val.jsonl")
        out_dir = workdir / f"f{i}_out"
        train_val = run_candidate(Path(train_py), train_path, out_dir, seed=0)
        model = out_dir / "model.joblib"
        if train_val == float("inf") or not model.exists():
            maes.append(float("inf"))
            continue
        try:
            maes.append(score_holdout(Path(train_py), model, val_path))
        except Exception:
            maes.append(float("inf"))
    return maes
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k candidate_fold -v`
Expected: 2 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): candidate_fold_maes — train.py 학습+holdout 채점 paired"
```

---

### Task 3: paired_comparison + verdict (통계)

**Files:**
- Modify: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_validation.py` 끝에 추가

```python
from pipeline.validation import paired_comparison, verdict


def test_paired_comparison_a_better_than_b():
    # a(winner)가 b(baseline)보다 일관되게 낮음 → mean_diff<0, CI가 0 미만
    a = [0.10, 0.11, 0.09, 0.12, 0.10]
    b = [0.15, 0.16, 0.14, 0.17, 0.15]
    c = paired_comparison(a, b, n_boot=2000, seed=0)
    assert c["mean_diff"] < 0
    assert c["ci_high"] < 0  # CI 전체가 0 미만 → 유의
    assert 0.0 <= c["wilcoxon_p"] <= 1.0
    assert c["effect_size"] < 0  # Cohen's dz 부호 = mean_diff 부호
    assert c["n_valid"] == 5


def test_paired_comparison_indistinguishable():
    a = [0.10, 0.11, 0.09, 0.12, 0.10]
    b = [0.10, 0.12, 0.08, 0.13, 0.09]  # 뒤섞임 → 차이가 0 근처
    c = paired_comparison(a, b, n_boot=2000, seed=0)
    assert c["ci_low"] < 0 < c["ci_high"]  # CI가 0을 포함


def test_verdict_branches():
    assert verdict({"wilcoxon_p": 0.01, "ci_low": -0.05, "ci_high": -0.01}) == "distinguishable"
    assert verdict({"wilcoxon_p": 0.4, "ci_low": -0.03, "ci_high": 0.02}) == "indistinguishable"
    assert verdict({"wilcoxon_p": 0.01, "ci_low": 0.01, "ci_high": 0.05}) == "worse"
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k "paired or verdict" -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 import + 함수 추가

상단 import에 추가:
```python
import numpy as np
from scipy.stats import wilcoxon
```

함수 추가:
```python
def paired_comparison(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 0) -> dict:
    """paired fold MAE 두 계열(a-b)의 평균차 bootstrap 95% CI + Wilcoxon p + Cohen's dz.

    a·b는 동일 fold에서 잰 유한 값이어야 한다(inf는 호출 전에 걸러짐 — gate가 처리).
    """
    diffs = np.array([x - y for x, y in zip(a, b)], dtype=float)
    mean_diff = float(diffs.mean())
    std = float(diffs.std(ddof=1)) if len(diffs) > 1 else 0.0
    effect_size = mean_diff / std if std > 0 else 0.0  # Cohen's dz

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diffs), size=(n_boot, len(diffs)))
    boot_means = diffs[idx].mean(axis=1)
    ci_low = float(np.percentile(boot_means, 2.5))
    ci_high = float(np.percentile(boot_means, 97.5))

    try:
        p = float(wilcoxon(a, b).pvalue)
    except ValueError:
        p = 1.0  # 전부 동일(차이 0) 등 → 구분 불가

    return {
        "mean_diff": mean_diff, "ci_low": ci_low, "ci_high": ci_high,
        "wilcoxon_p": p, "effect_size": effect_size, "n_valid": len(diffs),
    }


def verdict(comp: dict, alpha: float = 0.05) -> str:
    """winner(a) vs baseline(b) 판정. a-b 기준: 음수=winner가 낮음(좋음).

    distinguishable: 유의하게 낮음(p<alpha 그리고 CI 전체가 0 미만).
    worse: 유의하게 높음(p<alpha 그리고 CI 전체가 0 초과).
    그 외: indistinguishable.
    """
    sig = comp["wilcoxon_p"] < alpha
    if sig and comp["ci_high"] < 0:
        return "distinguishable"
    if sig and comp["ci_low"] > 0:
        return "worse"
    return "indistinguishable"
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k "paired or verdict" -v`
Expected: 3 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): paired_comparison(bootstrap+Wilcoxon+dz) + verdict"
```

---

### Task 4: run_validation_gate (오케스트레이션 + inf 처리)

**Files:**
- Modify: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — 끝에 추가

```python
from pipeline.validation import run_validation_gate


def test_run_validation_gate_baseline_vs_itself(tmp_path):
    # winner == baseline (같은 train.py) → 구분 불가가 정상
    rows = _rows(40)
    res = run_validation_gate(
        REPO / "train.py", REPO / "train.py", rows, tmp_path / "gate",
        k=5, repeats=1, n_boot=1000,
    )
    assert res["verdict_vs_baseline"] == "indistinguishable"
    assert abs(res["winner_vs_baseline"]["mean_diff"]) < 0.05
    assert res["n_failed_winner"] == 0
    assert len(res["winner_folds"]) == 5


def test_run_validation_gate_unstable_winner(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    rows = _rows(40)
    res = run_validation_gate(
        broken, REPO / "train.py", rows, tmp_path / "gate2", k=5, repeats=1, n_boot=1000,
    )
    assert res["verdict_vs_baseline"] == "worse"  # 불안정 후보는 worse 처리
    assert res["n_failed_winner"] == 5
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k run_validation_gate -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 추가

```python
def run_validation_gate(winner_train_py, baseline_train_py, rows: list[dict], workdir: Path,
                        k: int = 5, repeats: int = 10, base_seed: int = 0,
                        n_boot: int = 10000) -> dict:
    """naive·baseline·winner를 동일 fold에서 평가하고 winner 기준 paired 판정을 산출.

    winner가 한 fold라도 실패(inf)하면 불안정으로 보고 verdict='worse'(검증 불가)로 처리한다.
    advisory — 승격 결정은 Operator(H-B).
    """
    workdir = Path(workdir)
    splits = fold_splits(len(rows), k=k, repeats=repeats, base_seed=base_seed)
    winner_folds = candidate_fold_maes(winner_train_py, rows, splits, workdir / "winner")
    baseline_folds = candidate_fold_maes(baseline_train_py, rows, splits, workdir / "baseline")
    naive_folds = naive_fold_maes(rows, splits)

    n_failed_winner = sum(1 for m in winner_folds if m == float("inf"))
    n_failed_baseline = sum(1 for m in baseline_folds if m == float("inf"))

    res = {
        "winner_folds": winner_folds, "baseline_folds": baseline_folds,
        "naive_folds": naive_folds, "n_failed_winner": n_failed_winner,
        "n_failed_baseline": n_failed_baseline, "n_folds": len(splits),
        "winner_vs_baseline": None, "winner_vs_naive": None,
        "verdict_vs_baseline": None, "single_design": True,
    }
    if n_failed_winner > 0 or n_failed_baseline > 0:
        res["verdict_vs_baseline"] = "worse"  # 검증 불가(불안정) → 보수적
        return res

    res["winner_vs_baseline"] = paired_comparison(winner_folds, baseline_folds, n_boot, base_seed)
    res["winner_vs_naive"] = paired_comparison(winner_folds, naive_folds, n_boot, base_seed)
    res["verdict_vs_baseline"] = verdict(res["winner_vs_baseline"])
    return res
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k run_validation_gate -v`
Expected: 2 PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): run_validation_gate — 3-way paired + inf 불안정 처리"
```

---

### Task 5: render_validation_report (마크다운 + 단일설계 경고)

**Files:**
- Modify: `src/pipeline/validation.py`
- Test: `tests/pipeline/test_validation.py`

- [ ] **Step 1: 실패 테스트 작성** — 끝에 추가

```python
from pipeline.validation import render_validation_report


def test_render_report_contains_warning_and_models():
    res = {
        "winner_folds": [0.10, 0.11], "baseline_folds": [0.12, 0.13],
        "naive_folds": [1.40, 1.42], "n_failed_winner": 0, "n_failed_baseline": 0,
        "n_folds": 2, "single_design": True,
        "winner_vs_baseline": {"mean_diff": -0.02, "ci_low": -0.03, "ci_high": -0.01,
                               "wilcoxon_p": 0.04, "effect_size": -1.2, "n_valid": 2},
        "winner_vs_naive": {"mean_diff": -1.30, "ci_low": -1.35, "ci_high": -1.25,
                            "wilcoxon_p": 0.04, "effect_size": -8.0, "n_valid": 2},
        "verdict_vs_baseline": "distinguishable",
    }
    md = render_validation_report(res)
    assert "distinguishable" in md
    assert "단일 설계" in md  # 정직성 경고 블록
    assert "naive" in md and "baseline" in md and "winner" in md
    assert "T4" in md  # held-out 설계는 T4 필요 명시
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k render_report -v`
Expected: FAIL — ImportError

- [ ] **Step 3: 구현** — `src/pipeline/validation.py`에 추가

```python
def _mean(xs):
    return sum(xs) / len(xs) if xs else float("inf")


def render_validation_report(res: dict) -> str:
    """승격 검증 게이트 리포트(advisory). Operator가 승격 판단 시 참고."""
    L = ["# 승격 검증 리포트 (advisory)", ""]
    L.append(f"- folds: {res['n_folds']} (repeated K-fold, paired)")
    L.append(f"- winner 실패 fold: {res['n_failed_winner']} / baseline 실패 fold: "
             f"{res['n_failed_baseline']}")
    L.append("")
    L.append("| 모델 | 평균 fold MAE |")
    L.append("|---|---|")
    L.append(f"| naive | {_mean(res['naive_folds']):.4f} |")
    L.append(f"| baseline | {_mean(res['baseline_folds']):.4f} |")
    L.append(f"| winner | {_mean(res['winner_folds']):.4f} |")
    L.append("")
    wb = res["winner_vs_baseline"]
    if wb:
        L.append(f"**winner vs baseline**: mean_diff={wb['mean_diff']:+.4f} "
                 f"(95% CI [{wb['ci_low']:+.4f}, {wb['ci_high']:+.4f}]), "
                 f"Wilcoxon p={wb['wilcoxon_p']:.3f}, Cohen's dz={wb['effect_size']:+.2f}")
        wn = res["winner_vs_naive"]
        L.append(f"**winner vs naive**: mean_diff={wn['mean_diff']:+.4f} "
                 f"(95% CI [{wn['ci_low']:+.4f}, {wn['ci_high']:+.4f}]), "
                 f"Wilcoxon p={wn['wilcoxon_p']:.3f}")
    L.append("")
    L.append(f"## verdict (winner vs baseline): **{res['verdict_vs_baseline']}**")
    L.append("")
    L.append("> ⚠️ **단일 설계(n=53) 한계**: 본 검증은 한 설계 내 repeated K-fold일 뿐,")
    L.append("> 일반화(다른 설계 예측)를 주장하지 않는다. held-out *설계* 교차검증은 **T4**의 몫.")
    L.append("> verdict는 advisory — 승격 결정은 Operator(H-B).")
    return "\n".join(L)
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_validation.py -k render_report -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/validation.py tests/pipeline/test_validation.py
git commit -m "feat(validation): render_validation_report + 단일설계 경고"
```

---

### Task 6: operator_gate 연동 (승격 전 리포트 표시)

**Files:**
- Modify: `src/pipeline/operator_gate.py:10-17` (`summarize`)
- Test: `tests/pipeline/test_operator_gate.py`

- [ ] **Step 1: 실패 테스트 작성** — `tests/pipeline/test_operator_gate.py` 끝에 추가 (기존 import/헬퍼 재사용; Candidate 생성은 기존 테스트 패턴을 따른다)

```python
def test_summarize_includes_validation_report():
    from pipeline.candidate_gen import Candidate
    from pipeline.operator_gate import summarize

    winner = Candidate("cand-1", "moderate", "codex", "/tmp/1/train.py", "diff")
    ranking = [(winner, 0.10)]
    report = "# 승격 검증 리포트 (advisory)\nverdict: distinguishable"
    out = summarize(winner, 0.10, ranking, validation_report=report)
    assert "승격 검증 리포트" in out
    assert "distinguishable" in out
```

- [ ] **Step 2: 실패 확인**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -k validation_report -v`
Expected: FAIL — `summarize() got an unexpected keyword argument 'validation_report'`

- [ ] **Step 3: 구현** — `src/pipeline/operator_gate.py`의 `summarize` 시그니처/본문 수정

```python
def summarize(winner, val_mae, ranking, holdout_mae=None, validation_report=None) -> str:
    lines = [f"WINNER: {winner.id} ({winner.sdk}/{winner.strategy})  val_mae={val_mae:.4f}"]
    if holdout_mae is not None:
        lines.append(f"  holdout_mae={holdout_mae:.4f}  (val↔holdout 격차로 과적합 점검)")
    lines.append("RANKING:")
    for c, v in ranking:
        lines.append(f"  {c.id:>10}  {c.sdk}/{c.strategy:<12}  {v:.4f}")
    if validation_report is not None:
        lines.append("")
        lines.append(validation_report)
    return "\n".join(lines)
```

- [ ] **Step 4: 통과 확인**

Run: `uv run pytest tests/pipeline/test_operator_gate.py -v`
Expected: 모든 operator_gate 테스트 PASS (기존 + 신규)

- [ ] **Step 5: 커밋**

```bash
git add src/pipeline/operator_gate.py tests/pipeline/test_operator_gate.py
git commit -m "feat(operator_gate): summarize에 승격 검증 리포트 표시(advisory)"
```

---

### Task 7: 전체 회귀 + ruff green 게이트

**Files:** 없음 (검증만)

- [ ] **Step 1: 전체 테스트**

Run: `uv run pytest -q`
Expected: 모든 테스트 PASS (기존 45 + 신규 ~12). FAIL 시 해당 task 복귀.

- [ ] **Step 2: ruff**

Run: `make lint && make fmt`
Expected: ruff 통과. validation.py가 frozen 파일을 재포맷하지 않았는지 `git status` 확인 — frozen(train.py/prepare.py) 변경 시 `git restore`로 되돌릴 것.

- [ ] **Step 3: 정리 커밋(있으면)**

```bash
git add src/pipeline tests/pipeline && git commit -m "chore: ruff format validation 모듈" || echo "nothing to format"
```

---

### Task 8: gen-001 소급 재심 (usage, Operator 게이트)

**Files:**
- Create: `experiments/gen-001/revalidation.md`
- Modify: `experiments/gen-001/generation.json` (status — **Operator 승인 후에만**)

- [ ] **Step 1: 게이트를 gen-001에 적용** — pre-gen-001 baseline 소스 확보 후 실행

pre-gen-001 baseline(gen-001 이전 train.py)을 git 이력에서 추출:
```bash
cd /Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design
git show 619e24f~1:train.py > /tmp/pre_gen001_train.py 2>/dev/null \
  || git show gen-001-best~1:train.py > /tmp/pre_gen001_train.py
```
(619e24f = gen-001 winner 승격 커밋. 한 단계 전이 pre-gen-001 baseline. 실패 시 `git log --oneline -- train.py`로 직전 SHA를 찾아 사용.)

게이트 실행:
```bash
PYTHONPATH=src uv run python - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "src")
from pipeline.validation import run_validation_gate, render_validation_report
rows = [json.loads(l) for l in open("experiments/real-gcd-fargate/dataset/dataset.jsonl")]
res = run_validation_gate(
    Path("train.py"),                  # winner = 현 gen-001 winner
    Path("/tmp/pre_gen001_train.py"),  # baseline = pre-gen-001
    rows, Path("/tmp/gen001_reval"), k=5, repeats=10, n_boot=10000,
)
Path("experiments/gen-001/revalidation.md").write_text(
    render_validation_report(res) + "\n\n(생성: T1 검증 게이트, gen-001 소급 재심)\n"
)
print("verdict:", res["verdict_vs_baseline"])
PY
```

- [ ] **Step 2: 결과를 Operator에 보고** — verdict + 리포트를 제시. **status 변경/커밋은 Operator 승인 후에만**(H-B). 자율 판단 금지.

- [ ] **Step 3: (Operator 승인 시) 기록 커밋**

```bash
git add experiments/gen-001/revalidation.md experiments/gen-001/generation.json
git commit -m "experiment(gen-001): T1 검증 게이트 소급 재심 — verdict <...>"
```

- [ ] **Step 4: (Operator 승인 시) INTENT.md Learnings에 H-A 재심 결과 기록**

---

## Self-Review

- **Spec coverage**: D1 게이트=승격 전(Task6 연동·advisory) · D2 advisory(Task4 verdict는 자동거부 안 함, Task6 표시만) · D3 repeated 5-fold×10(Task1 `fold_splits` 기본값·Task4 repeats=10) · D4 3-way paired(Task4 run_validation_gate) · D5 Wilcoxon+bootstrap CI+Cohen's dz(Task3) · D6 단일설계 경고(Task5). §6 gen-001 재심=Task8. §7 테스트 전부 매핑. ✓
- **Placeholder scan**: 없음 — 모든 코드 step에 실제 코드. Task8의 pre-gen-001 SHA는 fallback 명령 포함(추측 아님). ✓
- **Type consistency**: `fold_splits`→`list[(list,list)]`, `candidate_fold_maes`/`naive_fold_maes`→`list[float]`, `paired_comparison`→dict(keys: mean_diff/ci_low/ci_high/wilcoxon_p/effect_size/n_valid), `verdict`→str, `run_validation_gate`→dict(winner_vs_baseline 등), `render_validation_report`→str, `summarize(..., validation_report=None)`. 전 task 일관. ✓
- **frozen 주의**: validation은 train.py/prepare.py/dataset를 읽기·임시분할만. Task7 Step2에서 ruff 재포맷이 frozen 파일을 건드리면 `git restore`(이전 이터레이션 사고 재발 방지). ✓
- **scipy 의존**: harness(Operator 소유) 모듈만 사용 — train.py 신규 의존성 금지 계약과 무관. sklearn 경유로 이미 설치됨(확인: scipy 1.17.1). ✓
