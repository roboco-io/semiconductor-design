"""Tests for scripts.inject_freshness (L2 freshness metadata hook).

Covers spec §4.1 per-node freshness invariants:
- last_ingested tracks source .md mtime (always refreshed)
- valid_from set on first ingest, preserved thereafter
- valid_to default null; manually-set values preserved
- idempotency on re-run when source mtime unchanged
- stderr warnings for unresolvable source_files
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ISO8601_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def _write_graph(path: Path, nodes: list[dict], edges: list[dict] | None = None) -> Path:
    path.write_text(json.dumps({"nodes": nodes, "edges": edges or []}))
    return path


def _touch(path: Path, mtime: float | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("stub content\n")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _node_by_id(graph: dict, node_id: str) -> dict:
    for n in graph["nodes"]:
        if n["id"] == node_id:
            return n
    raise KeyError(node_id)


def test_fresh_node_sets_last_ingested_equals_valid_from(tmp_path):
    from scripts.inject_freshness import inject_freshness

    src = _touch(tmp_path / "wiki" / "raw" / "alpha.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "n1", "source_file": "wiki/raw/alpha.md"}],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    node = _node_by_id(_load(graph_path), "n1")
    fresh = node["freshness"]
    assert fresh["last_ingested"] is not None
    assert fresh["valid_from"] == fresh["last_ingested"]
    assert fresh["valid_to"] is None
    assert ISO8601_RE.match(fresh["last_ingested"])
    assert src.exists()


def test_existing_node_preserves_valid_from_on_reingest(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "n1", "source_file": "a.md"}],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)
    first = _node_by_id(_load(graph_path), "n1")["freshness"]
    original_valid_from = first["valid_from"]

    _touch(tmp_path / "a.md", mtime=1_700_500_000.0)
    inject_freshness(graph_path, corpus_root=tmp_path)

    second = _node_by_id(_load(graph_path), "n1")["freshness"]
    assert second["valid_from"] == original_valid_from, "valid_from must be preserved"
    assert second["last_ingested"] != first["last_ingested"], "last_ingested should bump"
    assert second["valid_to"] is None


def test_manual_valid_to_preserved(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {
                "id": "n1",
                "source_file": "a.md",
                "freshness": {
                    "last_ingested": "2025-01-01T00:00:00+00:00",
                    "valid_from": "2025-01-01T00:00:00+00:00",
                    "valid_to": "2025-06-01T00:00:00+00:00",
                },
            }
        ],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    fresh = _node_by_id(_load(graph_path), "n1")["freshness"]
    assert fresh["valid_to"] == "2025-06-01T00:00:00+00:00"
    assert fresh["valid_from"] == "2025-01-01T00:00:00+00:00"


def test_null_valid_to_stays_null(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {
                "id": "n1",
                "source_file": "a.md",
                "freshness": {
                    "last_ingested": "2025-01-01T00:00:00+00:00",
                    "valid_from": "2025-01-01T00:00:00+00:00",
                    "valid_to": None,
                },
            }
        ],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    fresh = _node_by_id(_load(graph_path), "n1")["freshness"]
    assert fresh["valid_to"] is None


def test_iso8601_format(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "n1", "source_file": "a.md"}],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    fresh = _node_by_id(_load(graph_path), "n1")["freshness"]
    assert ISO8601_RE.match(fresh["last_ingested"])
    assert ISO8601_RE.match(fresh["valid_from"])
    # timezone suffix required (+00:00 or Z accepted; we emit +00:00)
    assert fresh["last_ingested"].endswith("+00:00") or fresh["last_ingested"].endswith("Z")


def test_multiple_source_files_uses_latest_mtime(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "old.md", mtime=1_700_000_000.0)
    _touch(tmp_path / "new.md", mtime=1_750_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {
                "id": "n1",
                "source_file": "old.md",
                "source_files": ["old.md", "new.md"],
            }
        ],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    fresh = _node_by_id(_load(graph_path), "n1")["freshness"]
    # mtime of new.md > old.md → last_ingested must reflect the newer file
    from datetime import datetime, timezone

    expected = datetime.fromtimestamp(1_750_000_000.0, tz=timezone.utc).isoformat()
    assert fresh["last_ingested"] == expected


def test_missing_source_file_yields_warning(tmp_path, capsys):
    from scripts.inject_freshness import inject_freshness

    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "n_missing", "source_file": "does_not_exist.md"}],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    captured = capsys.readouterr()
    assert "n_missing" in captured.err
    assert "WARN" in captured.err

    fresh = _node_by_id(_load(graph_path), "n_missing")["freshness"]
    assert fresh["last_ingested"] is None
    assert fresh["valid_from"] is None
    assert fresh["valid_to"] is None


def test_idempotency_double_run(tmp_path):
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "n1", "source_file": "a.md"}],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)
    first = _node_by_id(_load(graph_path), "n1")["freshness"]

    inject_freshness(graph_path, corpus_root=tmp_path)
    second = _node_by_id(_load(graph_path), "n1")["freshness"]

    assert first == second, "second run with unchanged mtime must be a no-op"


def test_malformed_graph_returns_error(tmp_path):
    """Exit code path: malformed JSON → main returns 1."""
    from scripts.inject_freshness import main

    bad = tmp_path / "graph.json"
    bad.write_text("{not json")

    rc = main(["--graph", str(bad), "--corpus-root", str(tmp_path)])
    assert rc == 1


def test_preserves_other_node_fields(tmp_path):
    """Only freshness dict is mutated — all other attrs untouched."""
    from scripts.inject_freshness import inject_freshness

    _touch(tmp_path / "a.md", mtime=1_700_000_000.0)
    graph_path = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {
                "id": "n1",
                "label": "alpha",
                "source_file": "a.md",
                "community": 42,
                "tier": "EXTRACTED",
                "norm_label": "alpha",
            }
        ],
        edges=[],
    )

    inject_freshness(graph_path, corpus_root=tmp_path)

    node = _node_by_id(_load(graph_path), "n1")
    assert node["label"] == "alpha"
    assert node["community"] == 42
    assert node["tier"] == "EXTRACTED"
    assert node["norm_label"] == "alpha"
    assert "freshness" in node
