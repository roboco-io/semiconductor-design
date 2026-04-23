"""Tests for scripts/compute_confidence.py — L2 Alternative B mapping.

Covers L2 derived spec §3.2 (tier × source_count → GOLD/SILVER/BRONZE) +
§3.3 #4 (source identity missing → excluded from count, promotion blocked) +
AMBIGUOUS row (confidence=None regardless of source_count).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from semi_design_runner.l2_schema import L2RecallNode


def _cli_argv() -> list[str]:
    """Resolve the `semi-confidence` console script or fall back to python -m.

    When tests run under `uv run pytest`, the installed entry point is on PATH.
    Fallback to `sys.executable -m scripts.compute_confidence` for environments
    where the wheel isn't installed but the repo is on PYTHONPATH.
    """
    cli = shutil.which("semi-confidence")
    if cli:
        return [cli]
    return [sys.executable, "-m", "scripts.compute_confidence"]


def _write_graph(path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}))
    return path


@pytest.fixture
def mixed_graph(tmp_path: Path) -> Path:
    """Graph covering each §3.2 row + §3.3 #4 edge case.

    Nodes (tier / expected):
      - n_ext2    EXTRACTED, reaches 2 distinct source_files → GOLD/0.95
      - n_ext1    EXTRACTED, reaches 1 source_file → SILVER/0.85
      - n_inf2    INFERRED,  reaches 2 distinct source_files → SILVER/0.85
      - n_inf1    INFERRED,  reaches 1 source_file → BRONZE/0.70
      - n_amb     AMBIGUOUS, reaches 2 source_files → confidence=None (§3.2 last row)
      - n_missing EXTRACTED, only connected to chunk without source_file → GOLD→SILVER downgrade
                  (because §3.3 #4: missing source identity chunk is excluded).
    """
    nodes = [
        # Row 1: EXTRACTED + 2 sources → GOLD
        {"id": "n_ext2", "tier": "EXTRACTED", "source_file": "papers/a.md"},
        {"id": "aux_ext2_b", "tier": "EXTRACTED", "source_file": "papers/b.md"},
        # Row 2: EXTRACTED + 1 source → SILVER (isolated; BFS yields only itself)
        {"id": "n_ext1", "tier": "EXTRACTED", "source_file": "papers/c.md"},
        # Row 3: INFERRED + 2 sources → SILVER
        {"id": "n_inf2", "tier": "INFERRED", "source_file": "papers/d.md"},
        {"id": "aux_inf2_e", "tier": "EXTRACTED", "source_file": "papers/e.md"},
        # Row 4: INFERRED + 1 source → BRONZE (isolated)
        {"id": "n_inf1", "tier": "INFERRED", "source_file": "papers/f.md"},
        # Row 5: AMBIGUOUS → confidence None regardless of source_count
        {"id": "n_amb", "tier": "AMBIGUOUS", "source_file": "papers/g.md"},
        {"id": "aux_amb_h", "tier": "EXTRACTED", "source_file": "papers/h.md"},
        # §3.3 #4 edge case: n_missing node itself has source_file; the only node
        # it can reach lacks source_file metadata. Missing chunk excluded →
        # source_count=1 → SILVER (GOLD→SILVER downgrade observable effect).
        {"id": "n_missing", "tier": "EXTRACTED", "source_file": "papers/i.md"},
        {"id": "aux_missing_nosrc", "tier": "EXTRACTED"},  # no source_file key
    ]
    edges = [
        {"source": "n_ext2", "target": "aux_ext2_b"},
        {"source": "n_inf2", "target": "aux_inf2_e"},
        {"source": "n_amb", "target": "aux_amb_h"},
        {"source": "n_missing", "target": "aux_missing_nosrc"},
    ]
    return _write_graph(tmp_path / "graph.json", nodes, edges)


def test_extracted_multi_source_yields_gold(mixed_graph):
    from scripts.compute_confidence import compute_node_confidence

    entry = compute_node_confidence(mixed_graph, "n_ext2")
    assert entry["tier"] == "EXTRACTED"
    assert entry["source_count"] == 2
    assert entry["confidence"] == "GOLD"
    assert entry["confidence_score"] == 0.95


def test_extracted_single_source_yields_silver(mixed_graph):
    from scripts.compute_confidence import compute_node_confidence

    entry = compute_node_confidence(mixed_graph, "n_ext1")
    assert entry["tier"] == "EXTRACTED"
    assert entry["source_count"] == 1
    assert entry["confidence"] == "SILVER"
    assert entry["confidence_score"] == 0.85


def test_inferred_multi_source_yields_silver(mixed_graph):
    from scripts.compute_confidence import compute_node_confidence

    entry = compute_node_confidence(mixed_graph, "n_inf2")
    assert entry["tier"] == "INFERRED"
    assert entry["source_count"] == 2
    assert entry["confidence"] == "SILVER"
    assert entry["confidence_score"] == 0.85


def test_inferred_single_source_yields_bronze(mixed_graph):
    from scripts.compute_confidence import compute_node_confidence

    # n_inf1 is isolated in the fixture → BFS yields only itself → 1 unique source.
    entry = compute_node_confidence(mixed_graph, "n_inf1")
    assert entry["tier"] == "INFERRED"
    assert entry["source_count"] == 1
    assert entry["confidence"] == "BRONZE"
    assert entry["confidence_score"] == 0.70


def test_ambiguous_yields_none_confidence(mixed_graph):
    from scripts.compute_confidence import compute_node_confidence

    entry = compute_node_confidence(mixed_graph, "n_amb")
    assert entry["tier"] == "AMBIGUOUS"
    assert entry["source_count"] == 2  # BFS still counts unique sources
    assert entry["confidence"] is None
    assert entry["confidence_score"] is None


def test_source_identity_missing_excluded_from_count(mixed_graph):
    """§3.3 #4: chunk without source_file metadata must not contribute to source_count.

    n_missing itself has source_file papers/i.md. It reaches aux_missing_nosrc
    (which lacks source_file). With §3.3 #4 enforcement, aux_missing_nosrc is
    excluded → source_count stays 1 → SILVER (not GOLD).
    """
    from scripts.compute_confidence import compute_node_confidence

    entry = compute_node_confidence(mixed_graph, "n_missing")
    assert entry["tier"] == "EXTRACTED"
    # source_count=1 because the missing-source-file chunk is excluded.
    assert entry["source_count"] == 1
    # GOLD→SILVER downgrade is the observable effect of the §3.3 #4 rule.
    assert entry["confidence"] == "SILVER"
    assert entry["confidence_score"] == 0.85
    assert entry["source_files"] == ["papers/i.md"]


def test_reproducibility_two_runs_same_output(mixed_graph):
    from scripts.compute_confidence import compute_all_confidence

    first = compute_all_confidence(mixed_graph)
    second = compute_all_confidence(mixed_graph)
    # Deterministic sort → exactly equal JSON dumps.
    assert json.dumps(first) == json.dumps(second)


def test_single_node_cli_mode(mixed_graph):
    result = subprocess.run(
        _cli_argv() + ["--graph", str(mixed_graph), "--node", "n_ext2"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    entry = json.loads(result.stdout)
    assert isinstance(entry, dict)
    assert entry["node_id"] == "n_ext2"
    assert entry["confidence"] == "GOLD"


def test_all_mode_emits_list(mixed_graph):
    result = subprocess.run(
        _cli_argv() + ["--graph", str(mixed_graph), "--all"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    entries = json.loads(result.stdout)
    assert isinstance(entries, list)
    # Sorted by node_id (deterministic).
    ids = [e["node_id"] for e in entries]
    assert ids == sorted(ids)
    # Every entry is L2RecallNode-compatible.
    for entry in entries:
        L2RecallNode(**entry)


def test_output_is_l2recallnode_compatible(mixed_graph):
    from scripts.compute_confidence import compute_all_confidence

    entries = compute_all_confidence(mixed_graph)
    # All entries round-trip through L2RecallNode.
    for entry in entries:
        node = L2RecallNode(**entry)
        assert node.node_id == entry["node_id"]
        assert node.tier == entry["tier"]
        # source_files is sorted alphabetically (determinism).
        if node.source_files:
            assert node.source_files == sorted(node.source_files)


def test_missing_node_errors(mixed_graph):
    """--node <unknown-id> → exit 1, error on stderr."""
    result = subprocess.run(
        _cli_argv() + ["--graph", str(mixed_graph), "--node", "does_not_exist"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "does_not_exist" in result.stderr


def test_networkx_links_key_supported(tmp_path):
    """Graph with 'links' key (NetworkX) must work identically to 'edges' key."""
    from scripts.compute_confidence import compute_node_confidence

    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "a", "tier": "EXTRACTED", "source_file": "papers/a.md"},
                    {"id": "b", "tier": "EXTRACTED", "source_file": "papers/b.md"},
                ],
                "links": [{"source": "a", "target": "b"}],
            }
        )
    )
    entry = compute_node_confidence(path, "a")
    assert entry["source_count"] == 2
    assert entry["confidence"] == "GOLD"
