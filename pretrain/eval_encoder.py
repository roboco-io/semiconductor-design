"""채택 게이트 일괄 판정 → encoder-v1.report.json에 verdict 병합 (spec §6.5)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pretrain_lib.embed import embed_endpoints, load_encoder  # noqa: E402
from pretrain_lib.encoder_gates import (  # noqa: E402
    collapse_diagnostics,
    encoder_verdict,
    linear_probe,
)
from pretrain_lib.manifest import load_manifest  # noqa: E402


@click.command()
@click.option("--encoder", required=True, type=click.Path(exists=True))
@click.option("--report", required=True, type=click.Path(exists=True))
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--corpus-dir", required=True, type=click.Path(exists=True))
@click.option("--label-dataset", required=True, type=click.Path(exists=True),
              help="v2 dataset.jsonl (emb_* 포함, 4설계 combine)")
def main(encoder, report, manifest, corpus_dir, label_dataset):
    model, vocab, config = load_encoder(encoder)
    m = load_manifest(manifest)
    embs = []
    for d in m["encoder_val_designs"]:  # spec §6.3: encoder-val 임베딩으로 진단
        nl = json.loads((Path(corpus_dir) / d / "netlist.json").read_text())
        embs += list(embed_endpoints(nl, model, vocab, config).values())
    diag = collapse_diagnostics(np.array(embs))
    rows = [json.loads(x) for x in Path(label_dataset).read_text().splitlines() if x.strip()]
    probe = linear_probe(rows)
    rep = json.loads(Path(report).read_text())
    verdict = encoder_verdict(rep, diag, probe)
    rep.update({"collapse": diag, "linear_probe": probe, "verdict": verdict})
    Path(report).write_text(json.dumps(rep, indent=2))
    click.echo(json.dumps(verdict))
    if not verdict["adopt"]:
        raise SystemExit(1)  # 기각 — 루프 투입 금지 (사전학습 반복/중단은 Operator 결정)


if __name__ == "__main__":
    main()
