"""prepare.py — EDA surrogate 데이터셋 준비 (frozen, 사람 유지 / NFR-2).

OD-1=per-path timing slack. 같은 flow 1회의 합성 후·라우팅 후 STA report_checks
두 리포트 → per-path feature + post-route slack label 데이터셋. 에이전트 변경 금지.
설계: docs/superpowers/plans/2026-06-04-prepare-py-dataset-generation.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

# 스크립트 직접 실행(`python prepare.py`) 시 pytest pythonpath가 적용되지 않으므로
# 자기 src 디렉터리를 import path에 부트스트랩한다.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from prepare_lib.dataset import build_dataset, write_dataset  # noqa: E402


@click.command()
@click.option("--synth", required=True, type=click.Path(exists=True), help="합성 후 STA report_checks")
@click.option("--route", required=True, type=click.Path(exists=True), help="라우팅 후 STA report_checks")
@click.option("--lockfile", required=True, type=click.Path(exists=True), help="flow lockfile (sha 앵커)")
@click.option("--design-id", required=True, help="source design 식별자")
@click.option("--out-dir", required=True, type=click.Path(), help="dataset.jsonl + manifest.json 출력 디렉터리")
@click.option("--netlist", type=click.Path(exists=True), default=None, help="netlist.json (v2: 임베딩 병기)")
@click.option("--encoder", type=click.Path(exists=True), default=None, help="frozen encoder .pt (v2)")
@click.option("--corpus-manifest", type=click.Path(exists=True), default=None,
              help="corpus_manifest.yaml (v2 sha 앵커)")
def main(synth: str, route: str, lockfile: str, design_id: str, out_dir: str,
         netlist: str | None, encoder: str | None, corpus_manifest: str | None) -> None:
    v2_opts = (netlist, encoder, corpus_manifest)
    if any(v2_opts) and not all(v2_opts):
        raise click.UsageError("--netlist/--encoder/--corpus-manifest는 셋 다 필요 (v2 모드)")
    if all(v2_opts):
        from prepare_lib.dataset import build_dataset_v2

        rows, manifest = build_dataset_v2(
            synth, route, lockfile, design_id, netlist, encoder, corpus_manifest
        )
    else:
        rows, manifest = build_dataset(synth, route, lockfile, design_id)
    write_dataset(rows, manifest, out_dir)
    click.echo(f"{manifest['n_samples']} samples → {out_dir} (sha {manifest['flow_lockfile_sha'][:12]})")


if __name__ == "__main__":
    main()
