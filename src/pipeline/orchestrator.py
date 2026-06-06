"""orchestrator — 1세대 루프: gen → run → select → 상태기록. 승격은 operator_gate(별도)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import click

from pipeline.candidate_gen import generate_candidates
from pipeline.runner import run_all
from pipeline.selection import select_winner


def run_generation(gen_no, dataset, baseline_train_py, program_md, n, gen_fn, out_root):
    gdir = Path(out_root) / f"gen-{gen_no:03d}"
    cdir = gdir / "candidates"
    cdir.mkdir(parents=True, exist_ok=True)
    baseline_src = Path(baseline_train_py).read_text(encoding="utf-8")

    cands = generate_candidates(baseline_src, program_md, cdir, n, gen_fn)
    results = run_all(cands, Path(dataset), cdir)
    winner, val, ranking = select_winner(results)

    with (gdir / "results.tsv").open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["id", "sdk", "strategy", "val_mae", "is_winner", "patch_ref"])
        for c, v in ranking:
            w.writerow([c.id, c.sdk, c.strategy, v, c is winner,
                        c.patch_ref.splitlines()[0] if c.patch_ref else ""])

    generation = {
        "gen_no": gen_no,
        "baseline_ref": str(baseline_train_py),
        "dataset": str(dataset),
        "winner_candidate_id": winner.id if winner else None,
        "winner_val_mae": val,
        "status": "awaiting_operator",
    }
    (gdir / "generation.json").write_text(json.dumps(generation, indent=2))
    return {"winner_id": winner.id if winner else None, "val_mae": val, "gen_dir": str(gdir)}


@click.command()
@click.option("--gen", "gen_no", required=True, type=int)
@click.option("--dataset", required=True, type=click.Path(exists=True))
@click.option("--n", default=4, type=int, help="후보 수")
@click.option("--out", "out_root", default="experiments", type=click.Path())
@click.option("--program", "program_md", default="program.md", type=click.Path(exists=True))
def main(gen_no, dataset, n, out_root, program_md):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from pipeline.sdk import claude_codex_gen_fn  # 실제 SDK (비용) — Operator 실행 시에만

    baseline = Path(__file__).resolve().parents[2] / "train.py"
    res = run_generation(gen_no, dataset, baseline, Path(program_md).read_text(),
                         n, claude_codex_gen_fn, out_root)
    click.echo(json.dumps(res, indent=2))
    click.echo("→ operator_gate로 검토·승인 후 promote (자율 머지 없음, H-B).")


if __name__ == "__main__":
    main()
