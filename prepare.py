"""prepare.py — EDA surrogate 데이터셋 준비 (frozen, 사람 유지 / NFR-2).

OD-1=per-path timing slack. 같은 flow 1회의 합성 후·라우팅 후 STA report_checks
두 리포트 → per-path feature + post-route slack label 데이터셋. 에이전트 변경 금지.
설계: docs/superpowers/plans/2026-06-04-prepare-py-dataset-generation.md
"""

from __future__ import annotations

import click

from prepare_lib.dataset import build_dataset, write_dataset


@click.command()
@click.option("--synth", required=True, type=click.Path(exists=True), help="합성 후 STA report_checks")
@click.option("--route", required=True, type=click.Path(exists=True), help="라우팅 후 STA report_checks")
@click.option("--lockfile", required=True, type=click.Path(exists=True), help="flow lockfile (sha 앵커)")
@click.option("--design-id", required=True, help="source design 식별자")
@click.option("--out-dir", required=True, type=click.Path(), help="dataset.jsonl + manifest.json 출력 디렉터리")
def main(synth: str, route: str, lockfile: str, design_id: str, out_dir: str) -> None:
    rows, manifest = build_dataset(synth, route, lockfile, design_id)
    write_dataset(rows, manifest, out_dir)
    click.echo(f"{manifest['n_samples']} samples → {out_dir} (sha {manifest['flow_lockfile_sha'][:12]})")


if __name__ == "__main__":
    main()
