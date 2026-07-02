"""corpus_manifest.yaml 로드·검증 — 코퍼스 구성이 사후 튜닝 노브가 되는 것을 차단 (spec §5)."""

from __future__ import annotations

from pathlib import Path

import yaml

# spec §5 사전 고정 — 이 둘 외의 제외 사유 금지.
FIXED_EXCLUSION_RULES = [
    "yosys synth exit code != 0",
    "extracted endpoints < 10",
]


def load_manifest(path: str | Path) -> dict:
    m = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    names = [d["name"] for d in m["designs"]]
    if len(names) != len(set(names)):
        raise ValueError("designs: 중복 설계 이름")
    if not str(m["orfs_image_digest"]).startswith("sha256:"):
        raise ValueError("orfs_image_digest: sha256 digest 필요")
    ev = m["encoder_val_designs"]
    if len(ev) != 2 or not set(ev) <= set(names):
        raise ValueError("encoder_val 설계는 designs 안의 2개여야 함 (spec §6.1)")
    if set(ev) & set(m["label_designs"]):
        raise ValueError("encoder_val 설계는 label 4설계와 겹칠 수 없음 (spec §6.1)")
    if m["exclusion_rules"] != FIXED_EXCLUSION_RULES:
        raise ValueError("exclusion_rules: spec §5 사전 고정 2건만 허용")
    for ex in m.get("exclusions", []):
        if not ex.get("design") or not ex.get("reason"):
            raise ValueError("exclusions: design·reason 필수")
    return m
