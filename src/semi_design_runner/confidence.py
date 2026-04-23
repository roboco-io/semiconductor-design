"""L2 Alternative B confidence computation (§3.2) — core logic.

Implements L2 derived spec §3.2 mapping:

    tier × source_count → confidence / confidence_score
    ---------------------------------------------------
    EXTRACTED ∧ ≥2 source  → GOLD   / 0.95
    EXTRACTED ∧  1 source  → SILVER / 0.85
    INFERRED  ∧ ≥2 source  → SILVER / 0.85
    INFERRED  ∧  1 source  → BRONZE / 0.70
    AMBIGUOUS ∧  *         → None   / None   (§3.2 last row)

`source_count` is computed by BFS from the target node over the graph's edges,
collecting the `source_file` attribute of every reachable node (including the
starting node). Nodes lacking `source_file` metadata are excluded from the
unique source set per §3.3 #4 (source identity requirement). This can cause a
GOLD→SILVER downgrade when the only extra source would come from a chunk
without source_file metadata.

Output is deterministic: source_files are sorted alphabetically and the
bulk output list is sorted by node_id. The same input graph.json always
produces the same output JSON.

Output fields mirror the `L2RecallNode` schema (required + provenance +
claim strength) so each entry round-trips through `L2RecallNode(**entry)`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

# §3.2 canonical mapping table. AMBIGUOUS is handled separately (always None/None).
_MAPPING: dict[tuple[str, bool], tuple[str, float]] = {
    ("EXTRACTED", True): ("GOLD", 0.95),  # ≥2 sources
    ("EXTRACTED", False): ("SILVER", 0.85),  # 1 source
    ("INFERRED", True): ("SILVER", 0.85),
    ("INFERRED", False): ("BRONZE", 0.70),
}


def _load_graph(graph_path: Path) -> tuple[dict[str, dict], list[dict]]:
    """Load graph.json, return (nodes_by_id, edges). Supports 'edges' and 'links'."""
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes", [])
    edges = graph.get("edges") or graph.get("links") or []
    nodes_by_id = {n["id"]: n for n in nodes}
    return nodes_by_id, edges


def _build_adjacency(edges: list[dict]) -> dict[str, set[str]]:
    """Undirected adjacency list from edges. Supports {source,target}."""
    adj: dict[str, set[str]] = {}
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src is None or tgt is None:
            continue
        adj.setdefault(src, set()).add(tgt)
        adj.setdefault(tgt, set()).add(src)
    return adj


def _bfs_sources(
    start: str,
    nodes_by_id: dict[str, dict],
    adj: dict[str, set[str]],
) -> list[str]:
    """BFS from start node; collect unique source_file values of reachable nodes.

    Nodes lacking `source_file` metadata are excluded per §3.3 #4. Cycles are
    handled by a visited set keyed on node_id.
    """
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    sources: set[str] = set()
    while queue:
        nid = queue.popleft()
        if nid in visited:
            continue
        visited.add(nid)
        node = nodes_by_id.get(nid)
        if node is not None:
            src = node.get("source_file")
            # §3.3 #4: exclude chunks without source_file metadata.
            if src:
                sources.add(src)
        for neighbor in adj.get(nid, ()):
            if neighbor not in visited:
                queue.append(neighbor)
    return sorted(sources)


def _apply_mapping(tier: str, source_count: int) -> tuple[str | None, float | None]:
    """Apply §3.2 table. AMBIGUOUS → (None, None) regardless of count."""
    if tier == "AMBIGUOUS":
        return None, None
    key = (tier, source_count >= 2)
    if key in _MAPPING:
        return _MAPPING[key]
    # Unknown tier → treat like AMBIGUOUS (conservative; should not happen on
    # a well-formed graphify output).
    return None, None


def _build_entry(
    node_id: str,
    nodes_by_id: dict[str, dict],
    adj: dict[str, set[str]],
) -> dict[str, Any]:
    node = nodes_by_id[node_id]
    tier = node.get("tier", "AMBIGUOUS")
    source_files = _bfs_sources(node_id, nodes_by_id, adj)
    source_count = len(source_files)
    confidence, confidence_score = _apply_mapping(tier, source_count)
    # Fields mirror L2RecallNode schema (required + provenance + claim strength).
    return {
        "node_id": node_id,
        "label": node.get("label", node_id),
        "source_file": node.get("source_file", ""),
        "tier": tier,
        "source_files": source_files,
        "source_count": source_count,
        "confidence": confidence,
        "confidence_score": confidence_score,
    }


def compute_node_confidence(graph_path: Path, node_id: str) -> dict[str, Any]:
    """Compute §3.2 confidence entry for a single node. Raises KeyError if missing."""
    nodes_by_id, edges = _load_graph(graph_path)
    if node_id not in nodes_by_id:
        raise KeyError(node_id)
    adj = _build_adjacency(edges)
    return _build_entry(node_id, nodes_by_id, adj)


def compute_all_confidence(graph_path: Path) -> list[dict[str, Any]]:
    """Compute §3.2 confidence entries for every node, sorted by node_id."""
    nodes_by_id, edges = _load_graph(graph_path)
    adj = _build_adjacency(edges)
    entries = [_build_entry(nid, nodes_by_id, adj) for nid in sorted(nodes_by_id)]
    return entries


def main(argv: list[str] | None = None) -> int:
    """CLI entry: `--graph <path>` + (`--node <id>` XOR `--all`). Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Compute L2 Alternative B confidence (§3.2) from graphify graph.json."
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path("graphify-out/graph.json"),
        help="Path to graphify graph.json (default: graphify-out/graph.json)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--node", type=str, help="Compute confidence for a single node_id")
    mode.add_argument("--all", action="store_true", help="Compute confidence for every node")
    args = parser.parse_args(argv)

    if not args.graph.exists():
        print(f"graph file not found: {args.graph}", file=sys.stderr)
        return 1

    try:
        if args.node is not None:
            entry = compute_node_confidence(args.graph, args.node)
            print(json.dumps(entry, sort_keys=True))
        else:
            entries = compute_all_confidence(args.graph)
            print(json.dumps(entries, sort_keys=True))
    except KeyError as exc:
        print(f"node_id not found in graph: {exc.args[0]}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, OSError) as exc:
        print(f"failed to load graph {args.graph}: {exc}", file=sys.stderr)
        return 1
    return 0
