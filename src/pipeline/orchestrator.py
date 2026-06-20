"""orchestrator — 1세대 루프: gen → run → select → 상태기록. 승격은 operator_gate(별도)."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import click

from pipeline import operator_gate
from pipeline.candidate_gen import generate_candidates
from pipeline.promotion_reviewer import review_promotion
from pipeline.report import render_generation_report
from pipeline.runner import run_all
from pipeline.selection import select_winner
from pipeline.validation import (
    render_crossdesign_report,
    render_validation_report,
    run_crossdesign_gate,
    run_crossdesign_validation_gate,
    run_validation_gate,
)


def run_generation(
    gen_no,
    dataset,
    baseline_train_py,
    program_md,
    n,
    gen_fn,
    out_root,
    seeds=(0, 1, 2, 3, 4),
    *,
    auto=False,
    gate_fn=None,
    lodo_gate_fn=None,
    reviewer_fn=None,
    do_git=True,
):
    gdir = Path(out_root) / f"gen-{gen_no:03d}"
    cdir = gdir / "candidates"
    cdir.mkdir(parents=True, exist_ok=True)
    baseline_src = Path(baseline_train_py).read_text(encoding="utf-8")

    cands = generate_candidates(baseline_src, program_md, cdir, n, gen_fn)
    results = run_all(cands, Path(dataset), cdir, seeds=seeds)
    winner, val, ranking = select_winner(results)

    with (gdir / "results.tsv").open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(
            ["id", "sdk", "strategy", "median_val_mae", "per_seed_vals", "is_winner", "patch_ref"]
        )
        for c, v, per_seed in ranking:
            w.writerow(
                [
                    c.id,
                    c.sdk,
                    c.strategy,
                    v,
                    json.dumps([v if v != float("inf") else None for v in per_seed]),
                    c is winner,
                    c.patch_ref.splitlines()[0] if c.patch_ref else "",
                ]
            )

    status = "awaiting_operator"
    lodo_res = None
    if auto and winner is None:
        status = "no_winner"
    if auto and winner is not None:
        rows = [json.loads(line) for line in Path(dataset).read_text().splitlines() if line.strip()]

        # --- LODO 교차설계 게이트 (T1 앞, 설계 ≥2일 때만) ---
        if len({r["group_key"] for r in rows}) >= 2:
            lgate = lodo_gate_fn or run_crossdesign_gate
            with tempfile.TemporaryDirectory(prefix=f"lodo-gen{gen_no:03d}-") as _ldir:
                lodo_res = lgate(Path(winner.src_path), Path(baseline_train_py), rows, Path(_ldir))
            lodo_report = render_crossdesign_report(lodo_res)
        else:
            # 단일 설계 — LODO 평가 불가(≥2 설계 필요). 리포트에 생략 사실 명기(spec §4.2).
            lodo_report = "LODO 생략 — 단일 설계 dataset (교차설계 평가 불가, ≥2 설계 필요)."

        # 실패 fold(부분 포함) 또는 worse/unverifiable → 차단(T1·Codex 생략, fail-fast).
        # "모든 fold가 유효해야 함"은 승격 게이트 정책 — probe 함수가 아니라 호출자(여기)가 강제.
        lodo_blocked = lodo_res is not None and (
            lodo_res["n_valid"] < lodo_res["n_designs"]
            or lodo_res["verdict"] in ("worse", "unverifiable")
        )

        if lodo_blocked:
            status = "rejected_lodo"
            t1_report = "LODO 게이트 미통과 — T1 생략."
            codex_verdict = {"approve": False, "reasons": "LODO 미통과 — 심사 생략"}
        else:
            # 다설계 → 교차설계 T1(repeated LODO), 단일설계 → 기존 혼합 K-fold T1 (spec §3.4).
            # gate_fn 주입 시 그대로(테스트 mock) — 기본값만 분기.
            if gate_fn is not None:
                gate = gate_fn
            elif len({r["group_key"] for r in rows}) >= 2:
                gate = run_crossdesign_validation_gate
            else:
                gate = run_validation_gate
            # T1 fold 작업물(50 fold × jsonl/joblib, 100MB+)은 임시 — tempdir에 쓰고 자동 정리.
            with tempfile.TemporaryDirectory(prefix=f"t1-gen{gen_no:03d}-") as _t1dir:
                t1 = gate(Path(winner.src_path), Path(baseline_train_py), rows, Path(_t1dir))
            t1_report = render_validation_report(t1)
            verdict = t1.get("verdict_vs_baseline")
            codex_verdict = {"approve": False, "reasons": "T1 미통과 — 심사 생략"}
            if verdict == "distinguishable":
                winner_src = Path(winner.src_path).read_text(encoding="utf-8")
                baseline_src_now = Path(baseline_train_py).read_text(encoding="utf-8")
                rfn = reviewer_fn
                if rfn is None:
                    from pipeline.sdk import codex_review_fn as rfn  # 실제 Codex (구독)
                codex_verdict = review_promotion(
                    winner_src, baseline_src_now, t1_report, reviewer_fn=rfn
                )
                if codex_verdict["approve"]:
                    operator_gate.promote(
                        Path(winner.src_path),
                        Path(baseline_train_py),
                        gen_no,
                        approved=True,
                        do_git=do_git,
                    )
                    status = "promoted"
                else:
                    status = "rejected_codex"
            else:
                status = "rejected_t1"

        # 다설계 dataset(LODO 실행됨)이면 비교성 경고를 리포트에 명기(spec §6).
        comparability_note = (
            "⚠️ 다설계 dataset 평가 — val_mae를 gen-001~003과 직접 비교 금지(설계 교체)."
            if lodo_res is not None
            else None
        )
        report_md = render_generation_report(
            gen_no,
            [(c.id, c.sdk, c.strategy, v) for c, v, _ps in ranking],
            winner.id,
            t1_report,
            codex_verdict,
            status,
            lodo_report=lodo_report,
            comparability_note=comparability_note,
        )
        (gdir / "report.md").write_text(report_md, encoding="utf-8")

    generation = {
        "gen_no": gen_no,
        "baseline_ref": str(baseline_train_py),
        "dataset": str(dataset),
        "metric": "median_val_mae",
        "eval_seeds": list(seeds),
        "winner_candidate_id": winner.id if winner else None,
        # float("inf") is not valid RFC 8259 — store null when no valid winner.
        "winner_val_mae": val if val != float("inf") else None,
        "status": status,
        "lodo_verdict": lodo_res["verdict"] if lodo_res else None,
        "lodo_n_valid": lodo_res["n_valid"] if lodo_res else None,
        "lodo_n_designs": lodo_res["n_designs"] if lodo_res else None,
    }
    (gdir / "generation.json").write_text(json.dumps(generation, indent=2))
    return {"winner_id": winner.id if winner else None, "val_mae": val, "gen_dir": str(gdir)}


@click.command()
@click.option("--gen", "gen_no", required=True, type=int)
@click.option("--dataset", required=True, type=click.Path(exists=True))
@click.option("--n", default=4, type=int, help="후보 수")
@click.option("--out", "out_root", default="experiments", type=click.Path())
@click.option("--program", "program_md", default="program.md", type=click.Path(exists=True))
@click.option("--auto", is_flag=True, default=False, help="자동 승격 게이트(median+T1+Codex) 활성")
def main(gen_no, dataset, n, out_root, program_md, auto):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from pipeline.sdk import claude_codex_gen_fn  # 실제 CLI 호출(구독 사용량) — Operator 실행 시에만

    baseline = Path(__file__).resolve().parents[2] / "train.py"
    res = run_generation(
        gen_no,
        dataset,
        baseline,
        Path(program_md).read_text(),
        n,
        claude_codex_gen_fn,
        out_root,
        auto=auto,
    )
    click.echo(json.dumps(res, indent=2))
    if auto:
        click.echo("→ 자동 게이트(median + T1 + Codex) 판정 완료. generation.json status 확인.")
    else:
        click.echo("→ operator_gate로 검토·승인 후 promote (자율 머지 없음, H-B).")


if __name__ == "__main__":
    main()
