"""L2 Substrate runtime — real implementation of the §3.2 v2 contract.

Implements the four interfaces from the overview spec §3.2 contract table:

  - ``L2.memory.recall(query)``      → recall()
  - ``L2.skill_library.query(...)``  → query()
  - ``L2.lint.check(graph_path)``    → lint_check()
  - ``L2.promotion_gate.check(node)``→ promotion_gate_check()  (L2 spec §3.3)

Plus the §5.3 ranking calibration and §6.3 freeze-authority assertions.

This module supersedes the in-test ``L2Runtime`` mock previously in
``tests/runner/test_l2_freeze.py``. The 8 regression tests there continue
to apply — re-run them against this module to verify §6.3 freeze rules.

§6.3 freeze layers (all three required):
  1. ``__slots__ = ()``       — instance attribute mutation → AttributeError
  2. ``_FrozenMeta``           — class attribute rebind → AttributeError
  3. ``MappingProxyType``       — weight table item-set → TypeError

§5.1 input validation:
  - query_text ≤ 500 chars   → ``QueryTooLong``
  - 1 ≤ k ≤ 50               → ``KOutOfRange``
  - 500 ≤ budget ≤ 32000     → ``BudgetOutOfRange``

§5.3 ranking score (per node):
  score = α · tier_weight + β · confidence_weight
        + γ · freshness_weight + δ · graph_centrality

MVP simplifications (documented for future enhancement):
  - Semantic match: label substring (case-insensitive). Embedding-based search
    is the spec's eventual target but graphify Python API does not yet expose
    a stable ``query()`` function — defer to follow-up.
  - graph_centrality: degree-centrality fallback when GRAPH_REPORT.md god-node
    rankings are unavailable. Falls back to 0.5 neutral baseline if the graph
    is too small for meaningful centrality.
  - freshness: nodes with no ``freshness.last_ingested`` field map to the
    ``fresh_180`` bucket (0.6) — L2 spec §4.2 specifies stale=0.3, but our
    current corpus is uniformly fresh; will reassess once decay is observed.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Optional

from semi_design_runner.confidence import (
    _build_adjacency,
    _build_entry,
    _load_graph,
)
from semi_design_runner.l2_schema import L2RecallNode

FREEZE_VIOLATION_MSG = "freeze 규칙 위반"
DEFAULT_GRAPH_PATH = Path("graphify-out/graph.json")


class QueryTooLong(ValueError):
    """Raised when query_text exceeds §5.1 ≤ 500 chars."""


class KOutOfRange(ValueError):
    """Raised when k is outside §5.1 [1, 50]."""


class BudgetOutOfRange(ValueError):
    """Raised when budget_tokens is outside §5.1 [500, 32000]."""


class _FrozenMeta(type):
    """Metaclass that blocks attribute rebinding on the class object itself.

    Without this, ``L2Runtime.ALPHA = 0.9`` would silently succeed (class
    attributes are mutable by default). §6.3 requires read-only — enforced
    structurally at the class level, not just by convention.
    """

    _initialized: bool = False

    def __setattr__(cls, name: str, value: Any) -> None:
        # Allow class body initialization once during class creation; block
        # rebinds thereafter. The _initialized flag flips at the bottom of
        # the L2Runtime definition.
        if getattr(cls, "_initialized", False) and not name.startswith("_"):
            raise AttributeError(f"{FREEZE_VIOLATION_MSG}: L2Runtime.{name} is read-only (§6.3)")
        super().__setattr__(name, value)


class L2Runtime(metaclass=_FrozenMeta):
    """L2 substrate runtime — real implementation.

    Stateless except for class-level constants. All methods are safe to call
    on either the class or an instance; instances exist only to satisfy
    ``rt = L2Runtime(); rt.recall(...)`` ergonomics. ``__slots__ = ()`` means
    instances carry no state — every L3 caller sees the same frozen weights.
    """

    __slots__ = ()

    # §5.3 ranking weights (frozen; change requires L2 spec re-approval).
    ALPHA: float = 0.30
    BETA: float = 0.30
    GAMMA: float = 0.20
    DELTA: float = 0.20

    # §5.3 per-category weight tables. MappingProxyType raises TypeError on
    # item-set, completing the third freeze layer (alongside __slots__ and
    # _FrozenMeta).
    TIER_WEIGHT: MappingProxyType = MappingProxyType(
        {"EXTRACTED": 1.0, "INFERRED": 0.7, "AMBIGUOUS": 0.0}
    )
    CONFIDENCE_WEIGHT: MappingProxyType = MappingProxyType(
        {"GOLD": 0.95, "SILVER": 0.85, "BRONZE": 0.70, None: 0.0}
    )
    FRESHNESS_WEIGHT: MappingProxyType = MappingProxyType(
        {"fresh_30": 1.0, "fresh_90": 0.8, "fresh_180": 0.6, "stale": 0.3}
    )

    # §5.1 query semantics defaults + bounds.
    K_DEFAULT: int = 10
    BUDGET_TOKENS_DEFAULT: int = 8000
    QUERY_TEXT_MAX_CHARS: int = 500
    K_MIN: int = 1
    K_MAX: int = 50
    BUDGET_MIN: int = 500
    BUDGET_MAX: int = 32000

    # §3.2 lint thresholds (mirror scripts/graph_integrity_check.py).
    AMBIGUOUS_THRESHOLD: float = 0.3

    # ------------------------------------------------------------------
    # L2.memory.recall — overview §3.2 v2 + L2 spec §5.1 / §5.2 / §5.3
    # ------------------------------------------------------------------

    def recall(
        self,
        query_text: str,
        *,
        k: int | None = None,
        budget_tokens: int | None = None,
        weights: dict[str, float] | None = None,
        graph_path: Path | None = None,
    ) -> list[L2RecallNode]:
        """Return top-k L2RecallNode list ranked by §5.3 weighted score.

        Validation per §5.1:
          - len(query_text) ≤ 500   → QueryTooLong
          - 1 ≤ k ≤ 50              → KOutOfRange
          - 500 ≤ budget ≤ 32000    → BudgetOutOfRange

        ``weights`` override is forbidden (§6.3). Pass None or omit.

        ``graph_path`` defaults to ``graphify-out/graph.json``. Tests supply
        a fixture path here.

        MVP semantic match: case-insensitive substring on node.label. Real
        embedding search is the spec's eventual target — see module docstring.
        """
        if weights is not None:
            raise RuntimeError(
                f"{FREEZE_VIOLATION_MSG}: weights override forbidden on L2.memory.recall (§6.3)"
            )

        # §5.1 input validation.
        if len(query_text) > self.QUERY_TEXT_MAX_CHARS:
            raise QueryTooLong(
                f"query_text length {len(query_text)} exceeds "
                f"{self.QUERY_TEXT_MAX_CHARS} chars (§5.1)"
            )
        k_val = self.K_DEFAULT if k is None else k
        if not (self.K_MIN <= k_val <= self.K_MAX):
            raise KOutOfRange(f"k={k_val} outside [{self.K_MIN}, {self.K_MAX}] (§5.1)")
        budget_val = self.BUDGET_TOKENS_DEFAULT if budget_tokens is None else budget_tokens
        if not (self.BUDGET_MIN <= budget_val <= self.BUDGET_MAX):
            raise BudgetOutOfRange(
                f"budget_tokens={budget_val} outside [{self.BUDGET_MIN}, {self.BUDGET_MAX}] (§5.1)"
            )

        gp = graph_path or DEFAULT_GRAPH_PATH
        nodes_by_id, edges = _load_graph(gp)
        adj = _build_adjacency(edges)

        query_lower = query_text.lower()
        candidates: list[tuple[float, L2RecallNode]] = []

        for node_id, raw_node in nodes_by_id.items():
            label = raw_node.get("label", node_id)
            if query_lower and query_lower not in label.lower():
                continue

            entry = _build_entry(node_id, nodes_by_id, adj)
            tier = entry["tier"]

            # §5.3 admissibility: AMBIGUOUS may appear in recall output (parent
            # contract permits it) but its tier_weight=0 ensures bottom rank.
            recall_node = L2RecallNode(
                node_id=entry["node_id"],
                label=entry["label"],
                source_file=entry["source_file"] or "",
                tier=tier,
                snippet=raw_node.get("snippet"),
                source_files=entry["source_files"],
                source_count=entry["source_count"],
                confidence=entry["confidence"],
                confidence_score=entry["confidence_score"],
                last_ingested=_node_freshness_field(raw_node, "last_ingested"),
                valid_from=_node_freshness_field(raw_node, "valid_from"),
                valid_to=_node_freshness_field(raw_node, "valid_to"),
                age_days=_compute_age_days(raw_node),
            )
            score = self.compute_score(recall_node, raw_node, adj)
            candidates.append((score, recall_node))

        # §5.3 top-k cut-off. Sort by score desc, stable on node_id for
        # determinism when scores tie.
        candidates.sort(key=lambda pair: (-pair[0], pair[1].node_id))
        return [n for _, n in candidates[:k_val]]

    # ------------------------------------------------------------------
    # L2.skill_library.query — overview §3.2 v2
    # ------------------------------------------------------------------

    def query(
        self,
        spec_uri: str,
        *,
        weights: dict[str, float] | None = None,
        graph_path: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Return skill metadata list for ``spec_uri`` context.

        ``weights`` override is forbidden (§6.3). Pass None or omit.

        MVP behavior: load graph, filter nodes whose label starts with
        ``skill:`` (per overview §5.1 convention), return their metadata
        dicts. graphify-side ``skill:<name>`` label prefix discipline is the
        single contract — semantic skill matching is a follow-up issue.

        Output schema per §3.2: ``{skill_id, patch_uri, signed_off_report_uri,
        tier, last_verified}``. Fields the graph does not carry (e.g.
        ``patch_uri``) are returned as None — caller may filter or warn.
        """
        if weights is not None:
            raise RuntimeError(
                f"{FREEZE_VIOLATION_MSG}: weights override forbidden on "
                f"L2.skill_library.query (§6.3)"
            )
        del spec_uri  # MVP ignores spec_uri context — returns all skills.

        gp = graph_path or DEFAULT_GRAPH_PATH
        nodes_by_id, _edges = _load_graph(gp)

        skills: list[dict[str, Any]] = []
        for node_id, raw_node in nodes_by_id.items():
            label = raw_node.get("label", "")
            if not label.startswith("skill:"):
                continue
            skills.append(
                {
                    "skill_id": label[len("skill:") :].strip() or node_id,
                    "patch_uri": raw_node.get("patch_uri"),
                    "signed_off_report_uri": raw_node.get("signed_off_report_uri"),
                    "tier": raw_node.get("tier"),
                    "last_verified": raw_node.get("last_verified"),
                }
            )
        skills.sort(key=lambda s: s["skill_id"])
        return skills

    # ------------------------------------------------------------------
    # L2.lint.check — overview §3.2 v2 + scripts/graph_integrity_check.py
    # ------------------------------------------------------------------

    def lint_check(
        self,
        graph_path: Path | None = None,
    ) -> dict[str, Any]:
        """Wrap ``check_graph_integrity`` with the §3.2 v2 output schema.

        Returns ``{ok, errors, metrics: {orphan_count, dangling_count,
        ambiguous_ratio}}`` per overview §3.2 contract row 4.
        """
        from scripts.graph_integrity_check import check_graph_integrity

        gp = graph_path or DEFAULT_GRAPH_PATH
        ok, errors = check_graph_integrity(gp, self.AMBIGUOUS_THRESHOLD)

        # Compute metrics fields independently so the output matches §3.2
        # even when the underlying script returns only ok+errors.
        graph = json.loads(gp.read_text())
        nodes = graph.get("nodes", [])
        edges = graph.get("edges") or graph.get("links") or []
        node_ids = {n["id"] for n in nodes}

        dangling_count = sum(
            1 for e in edges if e.get("source") not in node_ids or e.get("target") not in node_ids
        )
        referenced: set[str] = set()
        for e in edges:
            referenced.add(e.get("source"))
            referenced.add(e.get("target"))
        orphan_count = len(node_ids - referenced)
        ambiguous = sum(1 for n in nodes if n.get("tier") == "AMBIGUOUS")
        ambiguous_ratio = ambiguous / len(nodes) if nodes else 0.0

        return {
            "ok": ok,
            "errors": errors,
            "metrics": {
                "orphan_count": orphan_count,
                "dangling_count": dangling_count,
                "ambiguous_ratio": ambiguous_ratio,
            },
        }

    # ------------------------------------------------------------------
    # L2.promotion_gate.check — L2 spec §3.3 (gates 1-4; gate 5 elsewhere)
    # ------------------------------------------------------------------

    def promotion_gate_check(
        self,
        node: dict[str, Any] | L2RecallNode,
    ) -> tuple[bool, str | None]:
        """Validate L2 spec §3.3 promotion gate rules 1-4 on ``node``.

        Rule 5 (confidence ranking-only) is enforced at the §5.3 decision-input
        boundary parser, not here — see ``tests/runner/test_l2_isolation.py``.

        Accepts either an ``L2RecallNode`` or a dict shaped like
        ``compute_confidence`` output.
        """
        if isinstance(node, L2RecallNode):
            data = node.model_dump()
        else:
            data = node

        tier = data.get("tier")
        confidence = data.get("confidence")
        source_files = data.get("source_files") or []
        source_count = data.get("source_count")

        # Gate 4 — source identity. Empty source_files = unauditable.
        if not source_files:
            return False, "gate#4: source_files empty (source identity missing)"

        # Gate 4 supplementary — declared source_count must match len(source_files).
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
        self,
        graph_path: Path,
        node_id: str,
        declared_source_count: int,
    ) -> tuple[bool, str | None]:
        """Gate 1 — recompute source_count from graph; compare to declared.

        Separate from ``promotion_gate_check`` because it requires a live
        graph_path lookup (the other gates operate on a single node dict).
        """
        from semi_design_runner.confidence import compute_node_confidence

        recomputed = compute_node_confidence(graph_path, node_id)
        actual = recomputed["source_count"]
        if actual != declared_source_count:
            return False, (
                f"gate#1: reproducibility mismatch — declared source_count="
                f"{declared_source_count}, graph recomputation yielded {actual}"
            )
        return True, None

    # ------------------------------------------------------------------
    # §5.3 ranking score (used internally by recall, exposed for testing)
    # ------------------------------------------------------------------

    def compute_score(
        self,
        node: L2RecallNode,
        raw_node: dict[str, Any] | None = None,
        adj: dict[str, set[str]] | None = None,
    ) -> float:
        """Return the §5.3 weighted score for a single recall node.

        ``raw_node`` and ``adj`` are optional inputs used to compute graph
        centrality. When omitted, falls back to a neutral 0.5 baseline so
        the score is still well-defined for unit tests of the formula itself.
        """
        tier_w = self.TIER_WEIGHT.get(node.tier, 0.0)
        conf_w = self.CONFIDENCE_WEIGHT.get(node.confidence, 0.0)
        fresh_w = self._freshness_weight(node.age_days)
        cent = self._graph_centrality(node.node_id, raw_node, adj)
        return self.ALPHA * tier_w + self.BETA * conf_w + self.GAMMA * fresh_w + self.DELTA * cent

    @classmethod
    def _freshness_weight(cls, age_days: Optional[int]) -> float:
        """Map age_days to §5.3 freshness_weight bucket.

        None age_days → fresh_180 (0.6) — neutral default for nodes whose
        last_ingested is unknown. Stale (>180) only applies when age_days is
        explicitly recorded.
        """
        if age_days is None:
            return cls.FRESHNESS_WEIGHT["fresh_180"]
        if age_days <= 30:
            return cls.FRESHNESS_WEIGHT["fresh_30"]
        if age_days <= 90:
            return cls.FRESHNESS_WEIGHT["fresh_90"]
        if age_days <= 180:
            return cls.FRESHNESS_WEIGHT["fresh_180"]
        return cls.FRESHNESS_WEIGHT["stale"]

    @staticmethod
    def _graph_centrality(
        node_id: str,
        raw_node: dict[str, Any] | None,
        adj: dict[str, set[str]] | None,
    ) -> float:
        """Degree-centrality fallback in [0, 1].

        Spec §5.3 says "graphify god-node score normalized 0-1". MVP uses
        degree centrality (= len(adj[node_id]) / max_degree) when adjacency
        is available; otherwise neutral 0.5. Real god-node integration is a
        follow-up issue once GRAPH_REPORT.md JSON output stabilizes.
        """
        if adj is None or not adj:
            return 0.5
        degree = len(adj.get(node_id, ()))
        max_degree = max((len(neighbors) for neighbors in adj.values()), default=1)
        if max_degree == 0:
            return 0.5
        return degree / max_degree


# Flip the freeze switch after the class body completes. From this point
# forward ``L2Runtime.ATTR = value`` raises AttributeError.
_FrozenMeta._initialized = True  # type: ignore[attr-defined]


# ----------------------------------------------------------------------
# Helpers (module-private)
# ----------------------------------------------------------------------


def _node_freshness_field(raw_node: dict[str, Any], field: str) -> Optional[str]:
    """Read ``raw_node["freshness"][field]`` per scripts/inject_freshness.py layout."""
    fresh = raw_node.get("freshness")
    if not isinstance(fresh, dict):
        return None
    val = fresh.get(field)
    if val is None:
        return None
    return str(val)


def _compute_age_days(raw_node: dict[str, Any]) -> Optional[int]:
    """Compute age_days from freshness.last_ingested if present.

    last_ingested is ISO-8601 (date or full timestamp). Returns None when
    parsing fails so the caller falls back to neutral freshness.
    """
    iso = _node_freshness_field(raw_node, "last_ingested")
    if iso is None:
        return None
    try:
        if "T" in iso:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            ingested = dt.date()
        else:
            ingested = date.fromisoformat(iso)
    except (ValueError, TypeError):
        return None
    delta = date.today() - ingested
    return max(0, delta.days)
