"""combine — 설계별 dataset.jsonl을 다설계 결합 dataset으로 concat (Operator-owned).

각 파일은 한 설계(group_key 단일). 스키마 일치·설계 간 group_key 분리를 검증해 LODO 성립을 보장.
설계: docs/superpowers/specs/2026-06-09-t4-lite-suba-multidesign-data-design.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_KEYS = frozenset(
    [
        "endpoint",
        "endpoint_is_ff",
        "group_key",
        "max_stage_delay_ns",
        "mean_stage_delay_ns",
        "num_stages",
        "path_group",
        "post_route_slack_ns",
        "startpoint",
        "startpoint_is_ff",
        "synth_arrival_ns",
        "synth_slack_ns",
    ]
)


_EMB_RE = re.compile(r"^emb_\d{2}$")


def combine_datasets(paths: list[Path]) -> list[dict]:
    """여러 설계 dataset.jsonl을 입력 순서대로 concat. 스키마·group_key 분리·emb 키 일치 검증."""
    out, seen_groups = [], set()
    emb_keys: frozenset[str] | None = None  # 첫 파일 기준 — 설계 간 emb_dim 불일치 차단
    for path in paths:
        rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
        if not rows:
            raise ValueError(f"빈 dataset: {path}")
        file_groups = {r.get("group_key") for r in rows}
        for r in rows:
            keys = frozenset(r.keys())
            extra = keys - _KEYS
            if not _KEYS <= keys or any(not _EMB_RE.match(k) for k in extra):
                raise ValueError(f"스키마 불일치 {path}: {sorted(r.keys())}")
            if emb_keys is None:
                emb_keys = frozenset(extra)
            elif frozenset(extra) != emb_keys:
                raise ValueError(f"emb 키 불일치 {path}: {sorted(extra)}")
        if len(file_groups) != 1:
            raise ValueError(f"한 파일은 단일 설계여야 함 {path}: {file_groups}")
        g = next(iter(file_groups))
        if g in seen_groups:
            raise ValueError(f"group_key 중복(LODO 불가): {g}")
        seen_groups.add(g)
        out.extend(rows)
    return out
