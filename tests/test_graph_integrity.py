import json
from pathlib import Path


def _write_graph(path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}))
    return path


def test_clean_graph_passes(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "EXTRACTED"},
            {"id": "b", "tier": "INFERRED"},
        ],
        edges=[{"source": "a", "target": "b"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert ok, errors


def test_orphan_node_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "EXTRACTED"},
            {"id": "b", "tier": "INFERRED"},
            {"id": "orphan", "tier": "EXTRACTED"},
        ],
        edges=[{"source": "a", "target": "b"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert not ok
    assert any("orphan" in e.lower() for e in errors)


def test_dangling_edge_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[{"id": "a", "tier": "EXTRACTED"}],
        edges=[{"source": "a", "target": "nonexistent"}],
    )
    ok, errors = check_graph_integrity(graph)
    assert not ok
    assert any("dangling" in e.lower() for e in errors)


def test_ambiguous_ratio_exceeded_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "AMBIGUOUS"},
            {"id": "b", "tier": "AMBIGUOUS"},
            {"id": "c", "tier": "EXTRACTED"},
        ],
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "a"},
        ],
    )
    ok, errors = check_graph_integrity(graph, ambiguous_threshold=0.3)
    assert not ok
    assert any("AMBIGUOUS" in e for e in errors)


def test_ambiguous_ratio_within_threshold_passes(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(
        tmp_path / "graph.json",
        nodes=[
            {"id": "a", "tier": "AMBIGUOUS"},
            {"id": "b", "tier": "EXTRACTED"},
            {"id": "c", "tier": "EXTRACTED"},
            {"id": "d", "tier": "EXTRACTED"},
        ],
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
            {"source": "c", "target": "d"},
        ],
    )
    ok, errors = check_graph_integrity(graph, ambiguous_threshold=0.3)
    assert ok, errors


def test_empty_graph_fails(tmp_path):
    from scripts.graph_integrity_check import check_graph_integrity

    graph = _write_graph(tmp_path / "graph.json", nodes=[], edges=[])
    ok, errors = check_graph_integrity(graph)
    assert not ok


def test_networkx_links_key_supported(tmp_path):
    """graphify exports use NetworkX node_link_graph format with 'links' key."""
    import json as _json

    from scripts.graph_integrity_check import check_graph_integrity

    path = tmp_path / "graph.json"
    path.write_text(
        _json.dumps(
            {
                "nodes": [
                    {"id": "a", "tier": "EXTRACTED"},
                    {"id": "b", "tier": "INFERRED"},
                ],
                "links": [{"source": "a", "target": "b"}],
            }
        )
    )
    ok, errors = check_graph_integrity(path)
    assert ok, errors
