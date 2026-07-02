"""데이터셋 조립 + manifest + I/O (flow_lockfile_sha 재현성 앵커)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prepare_lib.report import parse_report
from prepare_lib.transform import FEATURE_NAMES, LABEL_NAME, join_paths


def flow_lockfile_sha(lockfile_path: str | Path) -> str:
    return hashlib.sha256(Path(lockfile_path).read_bytes()).hexdigest()


def build_dataset(
    synth_report: str | Path,
    route_report: str | Path,
    lockfile: str | Path,
    design_id: str,
) -> tuple[list[dict], dict]:
    synth = parse_report(Path(synth_report).read_text())
    route = parse_report(Path(route_report).read_text())
    rows = join_paths(synth, route)
    for r in rows:
        r["group_key"] = design_id  # OD-3 재설계: design 단위 group-disjoint
    sha = flow_lockfile_sha(lockfile)
    manifest = {
        "id": f"{design_id}-{sha[:12]}",
        "source_design": design_id,
        "feature_set": FEATURE_NAMES,
        "label_metric": LABEL_NAME,
        "flow_lockfile_sha": sha,
        "n_samples": len(rows),
    }
    return rows, manifest


def build_dataset_v2(
    synth_report: str | Path,
    route_report: str | Path,
    lockfile: str | Path,
    design_id: str,
    netlist_json: str | Path,
    encoder_path: str | Path,
    corpus_manifest_path: str | Path,
    min_coverage: float = 0.95,  # spec §8 amendment 복사 인용 — 재정의 금지
) -> tuple[list[dict], dict]:
    """v1 행에 frozen encoder 임베딩을 병기 — 같은 행·같은 라벨에서 표현만 다른 비교 (spec §5)."""
    import math

    from pretrain_lib.embed import embed_endpoints, load_encoder, sha256_file

    rows, manifest = build_dataset(synth_report, route_report, lockfile, design_id)
    model, vocab, config = load_encoder(encoder_path)
    embs = embed_endpoints(
        json.loads(Path(netlist_json).read_text(encoding="utf-8")), model, vocab, config
    )
    matched = []
    for r in rows:
        e = embs.get(r["endpoint"])
        # spec §8 NaN/inf 가드 — non-finite 임베딩 endpoint는 미매칭과 동일하게 drop(coverage 반영)
        if e is None or not all(math.isfinite(v) for v in e):
            continue
        matched.append({**r, **{f"emb_{i:02d}": v for i, v in enumerate(e)}})
    coverage = len(matched) / len(rows) if rows else 0.0
    if coverage < min_coverage:
        raise ValueError(
            f"emb coverage {coverage:.3f} < {min_coverage} — netlist/STA endpoint 이름 불일치 의심"
        )
    manifest = {
        **manifest,
        "n_samples": len(matched),
        "emb_dim": config["emb_dim"],
        "emb_coverage": round(coverage, 4),
        "encoder_sha": sha256_file(encoder_path),
        "corpus_manifest_sha": sha256_file(corpus_manifest_path),
    }
    return matched, manifest


def write_dataset(rows: list[dict], manifest: dict, out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dataset.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
