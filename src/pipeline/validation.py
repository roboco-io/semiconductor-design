"""validation — 승격 검증 게이트 (T1). naive·baseline·winner를 동일 fold에서 paired 비교.

advisory only — Operator 승격 결정(H-B)을 통계적 근거로 보조할 뿐 자동 거부하지 않는다.
train.py·prepare.py·dataset 무변경 (읽기 + 임시 fold 분할만).
설계: docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.holdout import score_holdout
from pipeline.runner import run_candidate
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
