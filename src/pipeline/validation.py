"""validation — 승격 검증 게이트 (T1). naive·baseline·winner를 동일 fold에서 paired 비교.

advisory only — Operator 승격 결정(H-B)을 통계적 근거로 보조할 뿐 자동 거부하지 않는다.
train.py·prepare.py·dataset 무변경 (읽기 + 임시 fold 분할만).
설계: docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from pipeline.holdout import score_holdout
from pipeline.runner import run_candidate
from scipy.stats import wilcoxon
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
