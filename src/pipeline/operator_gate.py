"""operator_gate — Operator 승인 게이트. 승인 시만 baseline 승격 + git tag (H-B)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def summarize(winner, val_mae, ranking, holdout_mae=None) -> str:
    lines = [f"WINNER: {winner.id} ({winner.sdk}/{winner.strategy})  val_mae={val_mae:.4f}"]
    if holdout_mae is not None:
        lines.append(f"  holdout_mae={holdout_mae:.4f}  (val↔holdout 격차로 과적합 점검)")
    lines.append("RANKING:")
    for c, v in ranking:
        lines.append(f"  {c.id:>10}  {c.sdk}/{c.strategy:<12}  {v:.4f}")
    return "\n".join(lines)


def promote(winner_src: Path, baseline: Path, gen_no: int,
            approved: bool, do_git: bool = True) -> bool:
    # 승인 전까지 baseline 불변 (자율 무인 머지 금지 — INTENT Not).
    if not approved:
        return False
    shutil.copyfile(winner_src, baseline)
    if do_git:
        subprocess.run(["git", "add", str(baseline)], check=True)
        subprocess.run(["git", "commit", "-m", f"feat(loop): gen-{gen_no:03d} winner 승격"], check=True)
        subprocess.run(["git", "tag", f"gen-{gen_no:03d}-best"], check=True)
    return True
