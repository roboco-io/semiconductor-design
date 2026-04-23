"""Regression tests for L2 spec §3.3 #5 — confidence isolation rule.

The L2 derived spec declares that `confidence`/`confidence_score` fields MUST
NOT flow into the overview spec §5.3 canonical decision table. These tests
encode that rule as schema-enforceable checks so an L3 implementer cannot
accidentally re-introduce the leak.

Covers:
  Test 1 — §5.3 decision-input parser drops confidence* fields from L2RecallNode.
  Test 2 — Overview spec §5.3 prose contains zero occurrences of confidence /
           GOLD / SILVER / BRONZE / support strength (Codex R3 "ranking only").
  Test 3 — §5.2 recall boundary still permits confidence on L2RecallNode (the
           isolation lives at §5.3, not at §5.2).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from semi_design_runner.l2_schema import L2RecallNode

# Absolute path to repo root (tests/runner/test_x.py → parents[2] == repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
OVERVIEW_SPEC = (
    REPO_ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-04-19-integrated-research-program-design.md"
)

# Substrings forbidden inside §5.3 per spec §3.3 #5 ("ranking only"). Both
# cased and lowercase variants are matched via case-insensitive regex.
FORBIDDEN_53_TOKENS: tuple[str, ...] = (
    "confidence",
    "GOLD",
    "SILVER",
    "BRONZE",
    "support strength",
)

# §5.3-approved fields the decision-input parser may expose. Anything else
# (especially confidence/confidence_score/source_count/etc.) must be dropped.
DECISION_INPUT_WHITELIST: frozenset[str] = frozenset(
    {"node_id", "label", "snippet", "source_files"}
)


class L2DecisionInputParser:
    """Reference implementation of the §5.3 decision-input boundary parser.

    Given an ``L2RecallNode`` (L2 §5.2 boundary), return the dict view that
    §5.3 canonical-decision-table inputs are allowed to see. Strips every
    field not in ``DECISION_INPUT_WHITELIST`` — in particular
    ``confidence`` / ``confidence_score`` (spec §3.3 #5) and the provenance/
    freshness metadata which are L2-internal ranking signals.
    """

    @staticmethod
    def parse(node: L2RecallNode) -> dict[str, Any]:
        full = node.model_dump()
        return {k: v for k, v in full.items() if k in DECISION_INPUT_WHITELIST}


def _extract_section_53(spec_text: str) -> str:
    """Return the §5.3 body (header + prose) up to the next ## heading.

    Robust to header casing/number: matches a line starting with ``### 5.3``
    (any trailing text) and stops at the next ``### 5.`` OR ``## `` line.
    """
    # Locate the §5.3 heading.
    header_re = re.compile(r"^### 5\.3\b.*$", re.MULTILINE)
    m = header_re.search(spec_text)
    if not m:
        raise AssertionError(
            "Could not find '### 5.3' heading in overview spec — spec layout may have changed."
        )
    start = m.start()
    # Stop at the next ### 5.X heading or a ## top-level heading.
    tail_re = re.compile(r"^(### 5\.[0-9]|## )", re.MULTILINE)
    m2 = tail_re.search(spec_text, pos=m.end())
    end = m2.start() if m2 else len(spec_text)
    return spec_text[start:end]


def test_decision_input_parser_drops_confidence_fields() -> None:
    """§3.3 #5: GOLD-tagged recall node stripped of confidence* at §5.3 boundary."""
    node = L2RecallNode(
        node_id="n-gold",
        label="Ahmed 2026 cross-tier confirmed example",
        source_file="wiki/raw/papers/k2-epsilon-ahmed-2026.md",
        tier="EXTRACTED",
        snippet="Cross-tier confirmed (≥2 independent sources).",
        source_files=[
            "wiki/raw/papers/k2-epsilon-ahmed-2026.md",
            "wiki/raw/papers/k2-epsilon-rasmussen-zep.md",
        ],
        source_count=2,
        confidence="GOLD",
        confidence_score=0.95,
        last_ingested="2026-04-22T10:15:00Z",
        age_days=1,
    )

    parsed = L2DecisionInputParser.parse(node)

    # Positive: the 4 whitelisted fields survive.
    assert parsed["node_id"] == "n-gold"
    assert parsed["label"].startswith("Ahmed 2026")
    assert parsed["snippet"] is not None
    assert parsed["source_files"] and len(parsed["source_files"]) == 2

    # Negative: every confidence*/provenance/freshness field was dropped.
    forbidden_keys = {
        "confidence",
        "confidence_score",
        "source_count",
        "tier",
        "source_file",
        "last_ingested",
        "valid_from",
        "valid_to",
        "age_days",
    }
    leaked = forbidden_keys & parsed.keys()
    assert not leaked, (
        f"§3.3 #5 isolation violation — decision-input parser leaked forbidden "
        f"field(s) {sorted(leaked)} into §5.3 input"
    )


def test_overview_spec_53_contains_no_confidence_tokens() -> None:
    """Static grep of overview §5.3 prose — spec §3.3 #5 "ranking only" rule.

    If this test fails, STOP and report the offending line(s). Do not edit
    the spec to silence the test — the coordinator decides.
    """
    assert OVERVIEW_SPEC.exists(), f"Overview spec missing at {OVERVIEW_SPEC}"
    spec_text = OVERVIEW_SPEC.read_text(encoding="utf-8")
    section_53 = _extract_section_53(spec_text)

    # Build a combined case-insensitive regex; report line numbers on match.
    pattern = re.compile("|".join(re.escape(tok) for tok in FORBIDDEN_53_TOKENS), re.IGNORECASE)
    offenders: list[tuple[int, str, str]] = []
    # Use finditer so every occurrence is reported, not just the first.
    for m in pattern.finditer(section_53):
        # Map character offset back to a 1-indexed line number inside §5.3.
        line_no = section_53.count("\n", 0, m.start()) + 1
        # Extract the line text for a readable failure message.
        line_start = section_53.rfind("\n", 0, m.start()) + 1
        line_end = section_53.find("\n", m.end())
        if line_end == -1:
            line_end = len(section_53)
        line_text = section_53[line_start:line_end]
        offenders.append((line_no, m.group(0), line_text.strip()))

    if offenders:
        report = "\n".join(
            f"  §5.3 line {ln}: token={tok!r} — {body}" for ln, tok, body in offenders
        )
        pytest.fail(
            "§3.3 #5 violation — overview spec §5.3 prose contains forbidden "
            "confidence*/tier-label tokens (ranking-only rule):\n" + report
        )


def test_recall_schema_permits_confidence_at_section_52_boundary() -> None:
    """§5.2 recall output schema still accepts confidence / confidence_score.

    The isolation applies at §5.3 (canonical decision input), not at §5.2
    (recall output). This guards against over-correction that would cripple
    recall ranking.
    """
    node = L2RecallNode(
        node_id="n-silver",
        label="INFERRED multi-source consensus",
        source_file="wiki/raw/papers/k2-epsilon-verga-poll.md",
        tier="EXTRACTED",
        confidence="GOLD",
        confidence_score=0.95,
    )
    # Pydantic validation passed (no exception) → schema permits confidence at §5.2.
    assert node.confidence == "GOLD"
    assert node.confidence_score == pytest.approx(0.95)
