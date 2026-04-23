"""Tests for L2.memory.recall output schema (L2RecallNode).

Covers L2 derived spec §5.2 (9 optional fields) + §3.3 #5 (confidence isolation)
+ §3.2 (tier × source_count mapping; AMBIGUOUS allows null confidence).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from semi_design_runner import l2_schema
from semi_design_runner.l2_schema import L2RecallNode, L2RecallResponse


def test_minimum_required_fields_roundtrip():
    """Only 4 required fields populated; dump → load → equal."""
    node = L2RecallNode(
        node_id="n1",
        label="OpenROAD STA",
        source_file="wiki/raw/papers/k2-zeta-openroad.md",
        tier="EXTRACTED",
    )
    dumped = node.model_dump()
    rebuilt = L2RecallNode.model_validate(dumped)
    assert rebuilt == node
    # Optional fields default to None
    assert rebuilt.snippet is None
    assert rebuilt.source_files is None
    assert rebuilt.source_count is None
    assert rebuilt.confidence is None
    assert rebuilt.confidence_score is None
    assert rebuilt.last_ingested is None
    assert rebuilt.valid_from is None
    assert rebuilt.valid_to is None
    assert rebuilt.age_days is None


def test_all_fields_roundtrip():
    """Every field populated; dump → load → equal."""
    node = L2RecallNode(
        node_id="n42",
        label="LibreLane 3.0.2 flow",
        source_file="wiki/raw/papers/k2-zeta-librelane.md",
        tier="INFERRED",
        snippet="LibreLane 3.0.2 replaces OpenLane2 (K2 ζ 2026-04-22).",
        source_files=[
            "wiki/raw/papers/k2-zeta-librelane.md",
            "wiki/raw/papers/k1-alpha-openlane2.md",
            "wiki/raw/sessions/phase-0-flow.md",
        ],
        source_count=3,
        confidence="GOLD",
        confidence_score=0.92,
        last_ingested="2026-04-22T10:15:00Z",
        valid_from="2026-04-01T00:00:00Z",
        valid_to="2026-10-01T00:00:00Z",
        age_days=1,
    )
    dumped = node.model_dump()
    rebuilt = L2RecallNode.model_validate(dumped)
    assert rebuilt == node
    # JSON round-trip too (catches serialization drift)
    as_json = node.model_dump_json()
    assert L2RecallNode.model_validate_json(as_json) == node


def test_invalid_tier_rejected():
    """tier must be one of EXTRACTED/INFERRED/AMBIGUOUS."""
    with pytest.raises(ValidationError):
        L2RecallNode(
            node_id="n1",
            label="x",
            source_file="f.md",
            tier="FOO",  # type: ignore[arg-type]
        )


def test_invalid_confidence_rejected():
    """confidence must be one of GOLD/SILVER/BRONZE or None."""
    with pytest.raises(ValidationError):
        L2RecallNode(
            node_id="n1",
            label="x",
            source_file="f.md",
            tier="EXTRACTED",
            confidence="PLATINUM",  # type: ignore[arg-type]
        )


def test_response_type_alias():
    """L2RecallResponse is list[L2RecallNode] and validates each element."""
    nodes = [
        L2RecallNode(node_id="a", label="A", source_file="a.md", tier="EXTRACTED"),
        L2RecallNode(node_id="b", label="B", source_file="b.md", tier="AMBIGUOUS"),
    ]
    payload: L2RecallResponse = nodes
    assert len(payload) == 2
    assert all(isinstance(n, L2RecallNode) for n in payload)
    # Type alias should resolve to list[L2RecallNode]
    # (runtime check: alias exists on module and equals list[L2RecallNode])
    assert l2_schema.L2RecallResponse == list[L2RecallNode]


def test_ambiguous_tier_allows_null_confidence():
    """§3.2 last row: AMBIGUOUS tier may have confidence=None (no claim to grade)."""
    node = L2RecallNode(
        node_id="n1",
        label="ambiguous fact",
        source_file="f.md",
        tier="AMBIGUOUS",
        confidence=None,
    )
    assert node.tier == "AMBIGUOUS"
    assert node.confidence is None


def test_freshness_iso8601_strings():
    """last_ingested / valid_from / valid_to are plain `str` (ISO-8601 convention)."""
    node = L2RecallNode(
        node_id="n1",
        label="x",
        source_file="f.md",
        tier="EXTRACTED",
        last_ingested="2026-04-22T10:15:00Z",
        valid_from="2026-04-01T00:00:00Z",
        valid_to="2026-10-01T00:00:00Z",
    )
    assert isinstance(node.last_ingested, str)
    assert isinstance(node.valid_from, str)
    assert isinstance(node.valid_to, str)


def test_module_docstring_declares_isolation():
    """§3.3 #5: confidence isolation rule must be encoded in module docstring."""
    doc = l2_schema.__doc__ or ""
    assert "confidence" in doc
    # Encodes the isolation warning (§3.3 #5): L1/L3 MUST NOT import confidence* fields.
    assert "MUST NOT import" in doc
    assert "L1.run" in doc and "L3.agent" in doc
