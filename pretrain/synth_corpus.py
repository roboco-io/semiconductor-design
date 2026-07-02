"""코퍼스 합성 드라이버 — ORFS docker(digest 고정)로 Yosys 합성만 → netlist.json (spec §4-[1]).

사람 소유. 실패 설계는 manifest exclusions에 사유 append 후 커밋(조용한 누락 금지, spec §5).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pretrain_lib.graph import build_endpoint_graphs  # noqa: E402
from pretrain_lib.manifest import load_manifest  # noqa: E402

IMAGE = "openroad/orfs"  # digest가 앵커 — 태그 아님
FLOW = "/OpenROAD-flow-scripts/flow"


def synth_one(design: dict, image: str, out_dir: Path, run=subprocess.run) -> dict:
    name, platform = design["name"], design["platform"]
    (Path(out_dir) / name).mkdir(parents=True, exist_ok=True)
    script = (
        # 이 ORFS 이미지의 synth 산출 netlist는 1_2_yosys.v (1_synth.v 아님 — 실측 2026-07-02)
        f"cd {FLOW} && make DESIGN_CONFIG=designs/{platform}/{name}/config.mk synth && "
        # flatten: -hier flow가 계층을 유지하므로 단일 모듈(graph.py 계약)로 평탄화
        f"yosys -p 'read_verilog results/{platform}/{name}/base/1_2_yosys.v; "
        f"hierarchy -auto-top; flatten; write_json /out/{name}/netlist.json'"
    )
    proc = run(
        ["docker", "run", "--rm", "--platform", "linux/amd64",
         "-v", f"{Path(out_dir).resolve()}:/out", image, "bash", "-lc", script],
        capture_output=True, text=True, timeout=14400,  # arm64 Mac x86 에뮬레이션 감안 4h
    )
    if proc.returncode != 0:
        return {"design": name, "ok": False, "reason": "yosys synth exit code != 0"}
    nl = Path(out_dir) / name / "netlist.json"
    if not nl.exists():
        return {"design": name, "ok": False, "reason": "yosys synth exit code != 0"}
    # spec §5 제외 규칙 (b) — 합성 워크플로에서 즉시 판정해 exclusion 기록을 완결.
    n_ep = len(build_endpoint_graphs(json.loads(nl.read_text(encoding="utf-8"))))
    if n_ep < 10:
        return {"design": name, "ok": False, "reason": "extracted endpoints < 10"}
    return {"design": name, "ok": True, "reason": ""}


@click.command()
@click.option("--manifest", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", required=True, type=click.Path())
@click.option("--designs", default="", help="쉼표 구분 부분 실행(기본: manifest 전체)")
def main(manifest: str, out_dir: str, designs: str) -> None:
    m = load_manifest(manifest)
    image = f"{IMAGE}@{m['orfs_image_digest']}"
    only = set(designs.split(",")) if designs else None
    results = []
    for d in m["designs"]:
        if only and d["name"] not in only:
            continue
        r = synth_one(d, image, Path(out_dir))
        results.append(r)
        click.echo(json.dumps(r))
    failed = [r for r in results if not r["ok"]]
    if failed:
        click.echo(f"⚠️ {len(failed)}건 실패 — corpus_manifest.yaml exclusions에 append 후 커밋 필요")


if __name__ == "__main__":
    main()
