"""Unit tests for the real L2Runtime — recall / query / lint / promotion_gate.

Covers behavior of ``semi_design_runner.l2_runtime.L2Runtime`` beyond the
§6.3 freeze-authority assertions in ``test_l2_freeze.py``:

- recall() input validation (§5.1) and §5.3 weighted-score ranking
- query() skill: prefix filter convention
- lint_check() output schema matches overview §3.2 v2 row 4
- promotion_gate_check() enforces L2 spec §3.3 gates 1-4
- compute_score() formula (α·tier + β·confidence + γ·freshness + δ·centrality)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from semi_design_runner.l2_runtime import (
    BudgetOutOfRange,
    KOutOfRange,
    L2Runtime,
    QueryTooLong,
)
from semi_design_runner.l2_schema import L2RecallNode


def _write_graph(tmp_path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    """Write a fixture graph.json with the given nodes/edges. Returns its path."""
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2))
    return graph_path


# ----------------------------------------------------------------------
# recall() — §5.1 input validation
# ----------------------------------------------------------------------


def test_recall_query_too_long_raises(tmp_path: Path) -> None:
    """query_text > 500 chars → QueryTooLong (§5.1)."""
    rt = L2Runtime()
    with pytest.raises(QueryTooLong, match="exceeds 500"):
        rt.recall("x" * 501)


def test_recall_k_out_of_range_raises(tmp_path: Path) -> None:
    """k=0 or k=51 → KOutOfRange (§5.1)."""
    graph_path = _write_graph(tmp_path, [], [])
    rt = L2Runtime()
    with pytest.raises(KOutOfRange):
        rt.recall("anything", k=0, graph_path=graph_path)
    with pytest.raises(KOutOfRange):
        rt.recall("anything", k=51, graph_path=graph_path)


def test_recall_budget_out_of_range_raises(tmp_path: Path) -> None:
    """budget_tokens=499 or 32001 → BudgetOutOfRange (§5.1)."""
    graph_path = _write_graph(tmp_path, [], [])
    rt = L2Runtime()
    with pytest.raises(BudgetOutOfRange):
        rt.recall("anything", budget_tokens=499, graph_path=graph_path)
    with pytest.raises(BudgetOutOfRange):
        rt.recall("anything", budget_tokens=32001, graph_path=graph_path)


# ----------------------------------------------------------------------
# recall() — §5.3 ranking + filter behavior
# ----------------------------------------------------------------------


def test_recall_filters_by_label_substring(tmp_path: Path) -> None:
    """Case-insensitive substring match on node.label (MVP semantic)."""
    nodes = [
        {
            "id": "n1",
            "label": "GCD floorplan density tuning",
            "tier": "EXTRACTED",
            "source_file": "wiki/raw/papers/k1-gamma.md",
        },
        {
            "id": "n2",
            "label": "AES key schedule",
            "tier": "EXTRACTED",
            "source_file": "wiki/raw/papers/k1-gamma.md",
        },
    ]
    edges = [{"source": "n1", "target": "n2"}]
    graph_path = _write_graph(tmp_path, nodes, edges)

    rt = L2Runtime()
    results = rt.recall("floorplan", graph_path=graph_path)
    assert len(results) == 1
    assert results[0].node_id == "n1"


def test_recall_returns_l2_recall_nodes_with_provenance(tmp_path: Path) -> None:
    """Recall output is a list of L2RecallNode with confidence/source fields populated."""
    nodes = [
        {
            "id": "n-gold",
            "label": "Cross-tier confirmed",
            "tier": "EXTRACTED",
            "source_file": "wiki/raw/papers/a.md",
        },
        {
            "id": "n-other",
            "label": "Cross-tier confirmed (companion)",
            "tier": "EXTRACTED",
            "source_file": "wiki/raw/papers/b.md",
        },
    ]
    edges = [{"source": "n-gold", "target": "n-other"}]
    graph_path = _write_graph(tmp_path, nodes, edges)

    rt = L2Runtime()
    results = rt.recall("cross-tier", graph_path=graph_path)
    assert all(isinstance(r, L2RecallNode) for r in results)
    by_id = {r.node_id: r for r in results}
    # Two distinct source files reachable via BFS → ≥2 → GOLD per Alternative B.
    assert by_id["n-gold"].confidence == "GOLD"
    assert by_id["n-gold"].source_count == 2


def test_recall_top_k_cutoff(tmp_path: Path) -> None:
    """k=2 returns only top 2 by score (§5.3 cutoff)."""
    nodes = [
        {"id": f"n{i}", "label": "match", "tier": "EXTRACTED", "source_file": f"f{i}.md"}
        for i in range(5)
    ]
    edges = [{"source": "n0", "target": "n1"}]  # only n0/n1 share BFS reach
    graph_path = _write_graph(tmp_path, nodes, edges)
    rt = L2Runtime()
    results = rt.recall("match", k=2, graph_path=graph_path)
    assert len(results) == 2


def test_recall_ranks_extracted_above_ambiguous(tmp_path: Path) -> None:
    """tier_weight: EXTRACTED=1.0, AMBIGUOUS=0.0 → EXTRACTED ranks higher."""
    nodes = [
        {"id": "ambig", "label": "match", "tier": "AMBIGUOUS", "source_file": "x.md"},
        {"id": "extracted", "label": "match", "tier": "EXTRACTED", "source_file": "y.md"},
    ]
    edges: list[dict] = []
    graph_path = _write_graph(tmp_path, nodes, edges)
    rt = L2Runtime()
    results = rt.recall("match", graph_path=graph_path)
    assert results[0].node_id == "extracted"
    assert results[1].node_id == "ambig"


# ----------------------------------------------------------------------
# query() — skill: prefix convention
# ----------------------------------------------------------------------


def test_query_returns_only_skill_prefixed_nodes(tmp_path: Path) -> None:
    """query() filters to label prefix 'skill:' per overview §5.1 convention."""
    nodes = [
        {
            "id": "s1",
            "label": "skill:gcd-floorplan-tweak",
            "tier": "EXTRACTED",
            "source_file": ".claude/skills/gcd-floorplan/SKILL.md",
        },
        {
            "id": "p1",
            "label": "paper: ORFS-agent 2025",
            "tier": "EXTRACTED",
            "source_file": "wiki/raw/papers/p.md",
        },
    ]
    graph_path = _write_graph(tmp_path, nodes, [])
    rt = L2Runtime()
    skills = rt.query("spec://anything", graph_path=graph_path)
    assert len(skills) == 1
    assert skills[0]["skill_id"] == "gcd-floorplan-tweak"


def test_query_output_schema_per_overview_3_2(tmp_path: Path) -> None:
    """Output dict has the 5 §3.2 keys (skill_id, patch_uri, signed_off_report_uri,
    tier, last_verified). Missing graph fields surface as None — caller filters."""
    nodes = [
        {"id": "s1", "label": "skill:foo", "tier": "EXTRACTED", "source_file": "a.md"},
    ]
    graph_path = _write_graph(tmp_path, nodes, [])
    rt = L2Runtime()
    skills = rt.query("spec://anything", graph_path=graph_path)
    assert set(skills[0].keys()) == {
        "skill_id",
        "patch_uri",
        "signed_off_report_uri",
        "tier",
        "last_verified",
    }
    assert skills[0]["tier"] == "EXTRACTED"


# ----------------------------------------------------------------------
# lint_check() — overview §3.2 v2 output schema
# ----------------------------------------------------------------------


def test_lint_check_output_shape(tmp_path: Path) -> None:
    """Output: {ok, errors, metrics: {orphan_count, dangling_count, ambiguous_ratio}}."""
    nodes = [
        {"id": "n1", "label": "a", "tier": "EXTRACTED", "source_file": "x.md"},
        {"id": "n2", "label": "b", "tier": "EXTRACTED", "source_file": "y.md"},
    ]
    edges = [{"source": "n1", "target": "n2"}]
    graph_path = _write_graph(tmp_path, nodes, edges)
    rt = L2Runtime()
    result = rt.lint_check(graph_path=graph_path)
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["metrics"]["orphan_count"] == 0
    assert result["metrics"]["dangling_count"] == 0
    assert result["metrics"]["ambiguous_ratio"] == 0.0


def test_lint_check_reports_orphans(tmp_path: Path) -> None:
    """Orphan node appears in metrics.orphan_count and errors include 'orphan'."""
    nodes = [
        {"id": "n1", "label": "a", "tier": "EXTRACTED", "source_file": "x.md"},
        {"id": "n2", "label": "b", "tier": "EXTRACTED", "source_file": "y.md"},
        {"id": "lonely", "label": "c", "tier": "EXTRACTED", "source_file": "z.md"},
    ]
    edges = [{"source": "n1", "target": "n2"}]
    graph_path = _write_graph(tmp_path, nodes, edges)
    rt = L2Runtime()
    result = rt.lint_check(graph_path=graph_path)
    assert result["ok"] is False
    assert result["metrics"]["orphan_count"] == 1
    assert any("orphan" in err for err in result["errors"])


def test_lint_check_reports_ambiguous_ratio(tmp_path: Path) -> None:
    """ambiguous_ratio computed as AMBIGUOUS_count / total_nodes."""
    nodes = [
        {"id": f"n{i}", "label": "a", "tier": "AMBIGUOUS", "source_file": f"x{i}.md"}
        for i in range(4)
    ] + [
        {"id": "ok", "label": "ok", "tier": "EXTRACTED", "source_file": "ok.md"},
    ]
    edges = [{"source": "n0", "target": "ok"}]
    graph_path = _write_graph(tmp_path, nodes, edges)
    rt = L2Runtime()
    result = rt.lint_check(graph_path=graph_path)
    # 4/5 = 0.8 > threshold 0.3 → fails AND ratio reported
    assert result["metrics"]["ambiguous_ratio"] == pytest.approx(0.8)
    assert result["ok"] is False


# ----------------------------------------------------------------------
# promotion_gate_check() — L2 spec §3.3 gates 1-4
# ----------------------------------------------------------------------


def test_promotion_gate_passes_clean_silver_node() -> None:
    """SILVER tier with single source_file passes (gates 2-4 satisfied)."""
    rt = L2Runtime()
    ok, reason = rt.promotion_gate_check(
        {
            "tier": "EXTRACTED",
            "confidence": "SILVER",
            "source_files": ["wiki/raw/papers/a.md"],
            "source_count": 1,
        }
    )
    assert ok is True
    assert reason is None


def test_promotion_gate_fails_gold_with_single_source() -> None:
    """Gate 2 — GOLD requires ≥2 distinct sources (Ahmed 2026)."""
    rt = L2Runtime()
    ok, reason = rt.promotion_gate_check(
        {
            "tier": "EXTRACTED",
            "confidence": "GOLD",
            "source_files": ["wiki/raw/papers/a.md"],
            "source_count": 1,
        }
    )
    assert ok is False
    assert "gate#2" in reason
    assert "GOLD" in reason


def test_promotion_gate_fails_ambiguous_with_confidence() -> None:
    """Gate 3 — AMBIGUOUS may not carry confidence (§3.2 last row)."""
    rt = L2Runtime()
    ok, reason = rt.promotion_gate_check(
        {
            "tier": "AMBIGUOUS",
            "confidence": "BRONZE",
            "source_files": ["wiki/raw/papers/a.md"],
            "source_count": 1,
        }
    )
    assert ok is False
    assert "gate#3" in reason


def test_promotion_gate_fails_empty_source_files() -> None:
    """Gate 4 — empty source_files = unauditable, regardless of tier/confidence."""
    rt = L2Runtime()
    ok, reason = rt.promotion_gate_check(
        {
            "tier": "EXTRACTED",
            "confidence": "SILVER",
            "source_files": [],
            "source_count": 0,
        }
    )
    assert ok is False
    assert "gate#4" in reason


def test_promotion_gate_fails_count_mismatch() -> None:
    """Gate 4 supplementary — declared source_count must equal len(source_files)."""
    rt = L2Runtime()
    ok, reason = rt.promotion_gate_check(
        {
            "tier": "EXTRACTED",
            "confidence": "SILVER",
            "source_files": ["a.md"],
            "source_count": 5,  # disagrees with len(source_files)=1
        }
    )
    assert ok is False
    assert "gate#4" in reason
    assert "disagrees" in reason


def test_promotion_gate_accepts_l2_recall_node_input() -> None:
    """Accepts an L2RecallNode instance (in addition to plain dict)."""
    node = L2RecallNode(
        node_id="n1",
        label="x",
        source_file="a.md",
        tier="EXTRACTED",
        confidence="SILVER",
        source_files=["a.md"],
        source_count=1,
    )
    rt = L2Runtime()
    ok, _reason = rt.promotion_gate_check(node)
    assert ok is True


# ----------------------------------------------------------------------
# compute_score() — §5.3 formula
# ----------------------------------------------------------------------


def test_compute_score_extracted_gold_high(tmp_path: Path) -> None:
    """EXTRACTED + GOLD gets near-max score: 0.30·1.0 + 0.30·0.95 + 0.20·fresh + 0.20·cent."""
    node = L2RecallNode(
        node_id="n1",
        label="x",
        source_file="a.md",
        tier="EXTRACTED",
        confidence="GOLD",
        source_files=["a.md", "b.md"],
        source_count=2,
        age_days=10,
    )
    rt = L2Runtime()
    score = rt.compute_score(node)
    # 0.30·1.0 + 0.30·0.95 + 0.20·1.0 (fresh_30) + 0.20·0.5 (centrality fallback)
    assert score == pytest.approx(0.30 + 0.285 + 0.20 + 0.10)


def test_compute_score_ambiguous_low() -> None:
    """AMBIGUOUS tier → tier_weight=0, confidence=None → confidence_weight=0."""
    node = L2RecallNode(
        node_id="n1",
        label="x",
        source_file="a.md",
        tier="AMBIGUOUS",
        confidence=None,
        source_files=["a.md"],
        source_count=1,
        age_days=200,  # → stale=0.3
    )
    rt = L2Runtime()
    score = rt.compute_score(node)
    # 0.30·0.0 + 0.30·0.0 + 0.20·0.3 + 0.20·0.5 (centrality fallback)
    assert score == pytest.approx(0.0 + 0.0 + 0.06 + 0.10)


def test_freshness_bucketing_matches_spec_53() -> None:
    """Internal helper: age_days bucketing matches §5.3 cutoffs."""
    fw = L2Runtime._freshness_weight
    assert fw(None) == 0.6  # neutral default for unknown age
    assert fw(0) == 1.0
    assert fw(30) == 1.0
    assert fw(31) == 0.8
    assert fw(90) == 0.8
    assert fw(91) == 0.6
    assert fw(180) == 0.6
    assert fw(181) == 0.3
