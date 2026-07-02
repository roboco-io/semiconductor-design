"""encoder 사전학습 CLI — 사람 소유 1회 실행 (spec §6). 에이전트 실행 금지."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch  # noqa: E402
from pretrain_lib.graph import build_endpoint_graphs  # noqa: E402
from pretrain_lib.manifest import load_manifest  # noqa: E402
from pretrain_lib.pretrain_loop import train_encoder  # noqa: E402

CONFIG = {"hidden": 64, "emb_dim": 32, "n_layers": 3, "max_depth": 8, "max_nodes": 256}


@click.command()
@click.option("--corpus-dir", required=True, type=click.Path(exists=True))
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--seed", default=0, type=int)
@click.option("--max-epochs", default=200, type=int)
def main(corpus_dir: str, manifest: str, out: str, seed: int, max_epochs: int) -> None:
    m = load_manifest(manifest)
    excluded = {e["design"] for e in m.get("exclusions", [])}
    graphs_by_design = {}
    for d in m["designs"]:
        name = d["name"]
        if name in excluded:
            continue
        nl = Path(corpus_dir) / name / "netlist.json"
        graphs = build_endpoint_graphs(
            json.loads(nl.read_text()), CONFIG["max_depth"], CONFIG["max_nodes"]
        )
        if len(graphs) < 10:  # spec §5 제외 규칙 (b) — manifest append는 Operator가 커밋
            raise SystemExit(f"{name}: endpoints {len(graphs)} < 10 — manifest 제외 필요")
        graphs_by_design[name] = graphs
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model, vocab, report = train_encoder(
        graphs_by_design, m["encoder_val_designs"], seed=seed,
        max_epochs=max_epochs, patience=10, device=device, **{
            k: CONFIG[k] for k in ("hidden", "emb_dim", "n_layers")
        },
    )
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "vocab": vocab, "config": CONFIG},
               out_dir / "encoder-v1.pt")
    (out_dir / "encoder-v1.report.json").write_text(json.dumps(report, indent=2))
    click.echo(json.dumps({"best_val_loss": report["best_val_loss"],
                           "naive_baseline_loss": report["naive_baseline_loss"],
                           "stopped_epoch": report["stopped_epoch"]}))


if __name__ == "__main__":
    main()
