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

_DENOM_EPS = 1e-9  # Cohen's dz std 가드: 부동소수점 잔차(≈1e-17)를 0으로 취급


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
    if len(a) != len(b):
        raise ValueError(f"paired_comparison: 길이 불일치 a={len(a)} b={len(b)}")
    diffs = np.array([x - y for x, y in zip(a, b)], dtype=float)
    mean_diff = float(diffs.mean())
    std = float(diffs.std(ddof=1)) if len(diffs) > 1 else 0.0
    effect_size = mean_diff / std if std > _DENOM_EPS else 0.0  # Cohen's dz

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
        "mean_diff": mean_diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "wilcoxon_p": p,
        "effect_size": effect_size,
        "n_valid": len(diffs),
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

    주의(정직한 서술): train.py(frozen)는 받은 fold-train을 *다시* 내부 0.75 분할하므로 모델은
    fold-train 100%가 아닌 ~75%로 학습된다. 즉 clean K-fold가 아니라 train.py 내부분할을 포함한
    nested resampling이다. fold-val은 train.py가 전혀 보지 않은 완전 held-out이라 paired 비교는 유효.
    train.py가 어떤 fold에서 실패하면 그 fold MAE = inf.
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


def run_validation_gate(
    winner_train_py,
    baseline_train_py,
    rows: list[dict],
    workdir: Path,
    k: int = 5,
    repeats: int = 10,
    base_seed: int = 0,
    n_boot: int = 10000,
) -> dict:
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
        "winner_folds": winner_folds,
        "baseline_folds": baseline_folds,
        "naive_folds": naive_folds,
        "n_failed_winner": n_failed_winner,
        "n_failed_baseline": n_failed_baseline,
        "n_folds": len(splits),
        "winner_vs_baseline": None,
        "winner_vs_naive": None,
        "verdict_vs_baseline": None,
        "single_design": True,
    }
    if n_failed_winner > 0 or n_failed_baseline > 0:
        res["verdict_vs_baseline"] = "worse"  # 검증 불가(불안정) → 보수적
        return res

    res["winner_vs_baseline"] = paired_comparison(winner_folds, baseline_folds, n_boot, base_seed)
    res["winner_vs_naive"] = paired_comparison(winner_folds, naive_folds, n_boot, base_seed)
    res["verdict_vs_baseline"] = verdict(res["winner_vs_baseline"])
    return res


def _mean(xs):
    return sum(xs) / len(xs) if xs else float("inf")


def render_validation_report(res: dict) -> str:
    """승격 검증 게이트 리포트(advisory). Operator가 승격 판단 시 참고."""
    L = ["# 승격 검증 리포트 (advisory)", ""]
    L.append(f"- folds: {res['n_folds']} (repeated K-fold, paired)")
    L.append(
        f"- winner 실패 fold: {res['n_failed_winner']} / baseline 실패 fold: "
        f"{res['n_failed_baseline']}"
    )
    L.append("")
    L.append("| 모델 | 평균 fold MAE |")
    L.append("|---|---|")
    L.append(f"| naive | {_mean(res['naive_folds']):.4f} |")
    L.append(f"| baseline | {_mean(res['baseline_folds']):.4f} |")
    L.append(f"| winner | {_mean(res['winner_folds']):.4f} |")
    L.append("")
    wb = res["winner_vs_baseline"]
    if wb:
        L.append(
            f"**winner vs baseline**: mean_diff={wb['mean_diff']:+.4f} "
            f"(95% CI [{wb['ci_low']:+.4f}, {wb['ci_high']:+.4f}]), "
            f"Wilcoxon p={wb['wilcoxon_p']:.3f}, Cohen's dz={wb['effect_size']:+.2f}"
        )
        wn = res["winner_vs_naive"]
        L.append(
            f"**winner vs naive**: mean_diff={wn['mean_diff']:+.4f} "
            f"(95% CI [{wn['ci_low']:+.4f}, {wn['ci_high']:+.4f}]), "
            f"Wilcoxon p={wn['wilcoxon_p']:.3f}"
        )
    L.append("")
    L.append(f"## verdict (winner vs baseline): **{res['verdict_vs_baseline']}**")
    if res.get("n_failed_winner", 0) > 0 or res.get("n_failed_baseline", 0) > 0:
        L.append("")
        L.append(
            f"> ⚠️ 실패 fold 존재 — 통계 검정 미실시(불안정). "
            f"winner 실패={res['n_failed_winner']}, baseline 실패={res['n_failed_baseline']}. "
            f"verdict 'worse'는 통계적 열등이 아니라 검증 불가를 뜻함."
        )
    L.append("")
    L.append("> ⚠️ 반복 K-fold는 train/val 중첩으로 fold 점수들이 **상관**된다 — bootstrap CI·Wilcoxon p는")
    L.append("> 독립 표본 가정보다 **낙관적**(불확실성 과소평가)일 수 있다. verdict는 보수적으로 해석.")
    L.append("")
    L.append("> ⚠️ **단일 설계(n=53) 한계**: 본 검증은 한 설계 내 repeated K-fold일 뿐,")
    L.append("> 일반화(다른 설계 예측)를 주장하지 않는다. held-out *설계* 교차검증은 **T4**의 몫.")
    L.append("> verdict는 advisory — 승격 결정은 Operator(H-B).")
    return "\n".join(L)
