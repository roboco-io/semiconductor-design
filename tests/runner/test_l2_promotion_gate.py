"""Regression tests for L2 spec §3.3 — 5 promotion-gate 차단 기준.

The L2 derived spec §3.3 lists 5 blocking rules that ``L2.promotion_gate
.check(node)`` must enforce in addition to overview §7.3. Until a dedicated
``L2.promotion_gate`` module lands, we encode the 5 rules as a test-local
helper and exercise each one with a crafted violation so the wiring stays
explicit.

Gate 1 — reproducibility: source_count recomputation must match.
Gate 2 — GOLD requires ≥ 2 sources (Ahmed 2026 cross-tier confirmed).
Gate 3 — AMBIGUOUS may not carry confidence (§3.2 last row).
Gate 4 — chunks missing source_file metadata are excluded; if exclusion
         drops the node below its claimed tier, gate fails.
Gate 5 — ranking-only isolation (covered in test_l2_isolation.py — A-Test 1).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.compute_confidence import compute_node_confidence


# Reference implementation of the 5 §3.3 gates. Implemented in the test
# module deliberately — promoting this to src/ requires its own issue so the
# canonical location can be designed alongside the real L2Runtime.
def validate_promotion_gate(node: dict[str, Any]) -> tuple[bool, str | None]:
    """Return (ok, reason_if_failed) per L2 spec §3.3 rules 1-4.

    Rule 5 (confidence ranking-only) is enforced at the §5.3 parser boundary,
    not here — see ``tests/runner/test_l2_isolation.py``.

    ``node`` is a dict shaped like ``L2RecallNode.model_dump()`` or a
    ``compute_confidence.py`` entry.
    """
    tier = node.get("tier")
    confidence = node.get("confidence")
    source_files = node.get("source_files") or []
    source_count = node.get("source_count")

    # Gate 4 — source identity. Empty source_files = unauditable.
    if not source_files:
        return False, "gate#4: source_files empty (source identity missing)"

    # Gate 4 supplementary — declared source_count must equal len(source_files).
    # (len(source_files) is the ground truth since compute_confidence dedupes.)
    if source_count is not None and source_count != len(source_files):
        return False, (
            f"gate#4: declared source_count={source_count} disagrees with "
            f"len(source_files)={len(source_files)}"
        )

    # Gate 3 — AMBIGUOUS must carry confidence=None (§3.2 last row).
    if tier == "AMBIGUOUS" and confidence is not None:
        return False, "gate#3: AMBIGUOUS tier cannot carry confidence"

    # Gate 2 — GOLD requires ≥2 distinct sources (Ahmed 2026 cross-tier).
    if confidence == "GOLD" and len(source_files) < 2:
        return False, (f"gate#2: GOLD requires >=2 sources, got {len(source_files)}")

    return True, None


def validate_reproducibility(
    graph_path: Path, node_id: str, declared_source_count: int
) -> tuple[bool, str | None]:
    """Gate 1 — recompute source_count from graph and compare to declared value."""
    recomputed = compute_node_confidence(graph_path, node_id)
    actual = recomputed["source_count"]
    if actual != declared_source_count:
        return False, (
            f"gate#1: reproducibility mismatch — declared source_count="
            f"{declared_source_count}, graph recomputation yielded {actual}"
        )
    return True, None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_graph(path: Path, nodes: list[dict], edges: list[dict]) -> Path:
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}))
    return path


@pytest.fixture
def gate1_graph(tmp_path: Path) -> Path:
    """Graph with a node whose real source_count is 2 (EXTRACTED → GOLD)."""
    nodes = [
        {"id": "n_real", "tier": "EXTRACTED", "source_file": "papers/a.md"},
        {"id": "n_real_neighbor", "tier": "EXTRACTED", "source_file": "papers/b.md"},
    ]
    edges = [{"source": "n_real", "target": "n_real_neighbor"}]
    return _write_graph(tmp_path / "graph.json", nodes, edges)


@pytest.fixture
def gate4_graph(tmp_path: Path) -> Path:
    """Fixture for gate#4: a node reaching a chunk without source_file metadata.

    The missing-source chunk is excluded → observable source_count=1 → SILVER.
    If a human promoted this to GOLD, gate#4/gate#2 combination flags it.
    """
    nodes = [
        {"id": "n_audit", "tier": "EXTRACTED", "source_file": "papers/x.md"},
        {"id": "aux_nosrc", "tier": "EXTRACTED"},  # no source_file key
    ]
    edges = [{"source": "n_audit", "target": "aux_nosrc"}]
    return _write_graph(tmp_path / "graph.json", nodes, edges)


# ---------------------------------------------------------------------------
# Gate #1 — reproducibility
# ---------------------------------------------------------------------------


def test_promotion_gate_1_reproducibility_fail(gate1_graph: Path) -> None:
    """Declared source_count that disagrees with graph recomputation → fail.

    Simulates a human/agent asserting source_count=5 on a node whose actual
    BFS-derived source_count is 2. Gate#1 recomputes from graph.json and
    catches the divergence.
    """
    declared = 5  # deliberate lie; real count is 2.
    ok, reason = validate_reproducibility(gate1_graph, "n_real", declared)
    assert not ok
    assert reason is not None
    assert "gate#1" in reason
    assert "reproducibility" in reason
    # And recomputation matches when declared is correct.
    ok_ok, _ = validate_reproducibility(gate1_graph, "n_real", 2)
    assert ok_ok


def test_promotion_gate_1_reproducibility_pass_on_match(gate1_graph: Path) -> None:
    """Gate#1 passes when declared source_count matches graph recomputation."""
    ok, reason = validate_reproducibility(gate1_graph, "n_real", 2)
    assert ok
    assert reason is None


# ---------------------------------------------------------------------------
# Gate #2 — GOLD ∧ source_count=1 → fail
# ---------------------------------------------------------------------------


def test_promotion_gate_2_gold_single_source_rejected() -> None:
    """Hand-crafted GOLD-with-1-source node is blocked by gate#2.

    ``compute_confidence.py`` never produces this combination (§3.2 mapping
    emits SILVER for EXTRACTED+1). Gate#2 is the defense against a human/
    agent that bypassed the computation and manually tagged a node GOLD.
    """
    bad_node = {
        "node_id": "n-manual-gold",
        "label": "Manually promoted GOLD with 1 source",
        "source_file": "papers/single.md",
        "tier": "EXTRACTED",
        "source_files": ["papers/single.md"],
        "source_count": 1,
        "confidence": "GOLD",  # violation — Ahmed 2026 requires cross-tier
        "confidence_score": 0.95,
    }
    ok, reason = validate_promotion_gate(bad_node)
    assert not ok
    assert reason is not None
    assert "gate#2" in reason
    assert "GOLD" in reason


# ---------------------------------------------------------------------------
# Gate #3 — AMBIGUOUS ∧ confidence != null → fail
# ---------------------------------------------------------------------------


def test_promotion_gate_3_ambiguous_with_confidence_rejected() -> None:
    """AMBIGUOUS-tier node may not carry a non-null confidence (§3.2)."""
    bad_node = {
        "node_id": "n-amb",
        "label": "Ambiguous with spurious BRONZE label",
        "source_file": "papers/a.md",
        "tier": "AMBIGUOUS",
        "source_files": ["papers/a.md", "papers/b.md"],
        "source_count": 2,
        "confidence": "BRONZE",  # violation — §3.2 last row says None
        "confidence_score": 0.70,
    }
    ok, reason = validate_promotion_gate(bad_node)
    assert not ok
    assert reason is not None
    assert "gate#3" in reason
    assert "AMBIGUOUS" in reason


def test_promotion_gate_3_ambiguous_with_null_confidence_ok() -> None:
    """Sanity check: AMBIGUOUS + confidence=None is the §3.2-compliant shape."""
    good_node = {
        "node_id": "n-amb-ok",
        "label": "Ambiguous claim pending human review",
        "source_file": "papers/a.md",
        "tier": "AMBIGUOUS",
        "source_files": ["papers/a.md"],
        "source_count": 1,
        "confidence": None,
        "confidence_score": None,
    }
    ok, reason = validate_promotion_gate(good_node)
    assert ok, reason


# ---------------------------------------------------------------------------
# Gate #4 — source identity missing → excluded; can trigger downgrade/fail
# ---------------------------------------------------------------------------


def test_promotion_gate_4_source_identity_missing_rejected(gate4_graph: Path) -> None:
    """Node reaching only a no-source-file chunk → excluded source → gate trips.

    The recomputed entry from ``compute_confidence`` produces source_count=1
    / SILVER. If someone manually asserts source_count=2 to cross the GOLD
    threshold, gate#1 + gate#4 both catch the fabrication.
    """
    entry = compute_node_confidence(gate4_graph, "n_audit")
    # compute_confidence correctly downgrades to SILVER.
    assert entry["source_count"] == 1
    assert entry["confidence"] == "SILVER"

    # Now craft a violation: human claimed 2 sources to reach GOLD.
    fabricated = dict(entry)
    fabricated["source_count"] = 2
    fabricated["confidence"] = "GOLD"
    fabricated["confidence_score"] = 0.95
    # source_files still holds only the 1 real entry (downgrade trace).

    ok, reason = validate_promotion_gate(fabricated)
    assert not ok
    # Detection surfaces via either gate#4 (count mismatch) or gate#2 (GOLD<2).
    assert reason is not None
    assert "gate#4" in reason or "gate#2" in reason


def test_promotion_gate_4_empty_source_files_rejected() -> None:
    """A node with source_files=[] is unauditable → gate#4 fail."""
    bad_node = {
        "node_id": "n-orphan",
        "label": "Node with no verifiable source",
        "source_file": "",
        "tier": "EXTRACTED",
        "source_files": [],
        "source_count": 0,
        "confidence": None,
        "confidence_score": None,
    }
    ok, reason = validate_promotion_gate(bad_node)
    assert not ok
    assert reason is not None
    assert "gate#4" in reason


# ---------------------------------------------------------------------------
# Gate #5 — ranking-only isolation (covered elsewhere)
# ---------------------------------------------------------------------------


def test_promotion_gate_5_is_covered_by_isolation_A1() -> None:
    """Gate#5 enforcement lives at the §5.3 decision-input parser boundary.

    It is tested in ``tests/runner/test_l2_isolation.py::
    test_decision_input_parser_drops_confidence_fields`` (A-Test 1) plus the
    static prose grep (A-Test 2). Keeping this docstring-only marker makes
    the §3.3 #5 mapping discoverable from inside the promotion-gate suite.
    """
    # Intentional pass — cross-reference only.
    pass
