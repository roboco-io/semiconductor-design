# experiments/multidesign/probe/run_probe.py
"""feature 정규화 probe 드라이버 — LODO 2-fold, naive 기준 사전 고정 판정.

Operator-owned 일회성 실험(루프 후보 아님). frozen 무변경 — 변형은 train.py 사본.
spec: docs/superpowers/specs/2026-06-11-feature-normalization-probe-design.md
"""

from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

import click

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
    if any(not math.isfinite(m) for m in variant_maes):
        return "unverifiable"
    wins = sum(1 for v, n in zip(variant_maes, naive_maes, strict=True) if v < n - _TIE_EPS)
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
