# tests/prepare/test_combine.py
import json
import pytest
from prepare_lib.combine import combine_datasets

KEYS = [
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


def _row(gk, i):
    return {
        k: (gk if k == "group_key" else (f"e{i}" if k in ("endpoint", "startpoint") else 0.1))
        for k in KEYS
    }


def _jsonl(tmp_path, name, rows):
    p = tmp_path / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_combine_concats_and_preserves_order(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0), _row("gcd", 1)])
    b = _jsonl(tmp_path, "b.jsonl", [_row("aes", 0)])
    rows = combine_datasets([a, b])
    assert len(rows) == 3
    assert [r["group_key"] for r in rows] == ["gcd", "gcd", "aes"]  # 입력 순서 보존


def test_combine_rejects_schema_mismatch(tmp_path):
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0)])
    bad = _jsonl(tmp_path, "bad.jsonl", [{"group_key": "aes", "x": 1}])  # 스키마 다름
    with pytest.raises(ValueError):
        combine_datasets([a, bad])


def test_combine_rejects_duplicate_group_key(tmp_path):
    # 서로 다른 파일이 같은 group_key → LODO 성립 안 함 → 거부
    a = _jsonl(tmp_path, "a.jsonl", [_row("gcd", 0)])
    b = _jsonl(tmp_path, "b.jsonl", [_row("gcd", 1)])
    with pytest.raises(ValueError):
        combine_datasets([a, b])
