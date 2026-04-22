"""Graph integrity check for graphify-generated graph.json.

Verifies three invariants:
1. No orphan nodes (every node has at least one incident edge)
2. No dangling edges (every edge references existing nodes)
3. AMBIGUOUS node ratio <= threshold (default 0.3)

Exits non-zero on any violation. Used as L2.lint.check() replacement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_AMBIGUOUS_THRESHOLD = 0.3


def check_graph_integrity(
    graph_path: Path,
    ambiguous_threshold: float = DEFAULT_AMBIGUOUS_THRESHOLD,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes", [])
    edges = graph.get("edges") or graph.get("links") or []

    if not nodes:
        return False, ["graph has no nodes"]

    node_ids = {n["id"] for n in nodes}

    for e in edges:
        if e["source"] not in node_ids:
            errors.append(f"dangling edge source: {e['source']} -> {e['target']}")
        if e["target"] not in node_ids:
            errors.append(f"dangling edge target: {e['source']} -> {e['target']}")

    referenced: set[str] = set()
    for e in edges:
        referenced.add(e["source"])
        referenced.add(e["target"])
    orphans = node_ids - referenced
    if orphans:
        sample = sorted(orphans)[:5]
        errors.append(f"orphan nodes ({len(orphans)}): {sample}")

    ambiguous = sum(1 for n in nodes if n.get("tier") == "AMBIGUOUS")
    ratio = ambiguous / len(nodes)
    if ratio > ambiguous_threshold:
        errors.append(
            f"AMBIGUOUS ratio {ratio:.2%} exceeds threshold {ambiguous_threshold:.2%}"
        )

    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path, help="Path to graphify-generated graph.json")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_AMBIGUOUS_THRESHOLD,
        help=f"AMBIGUOUS ratio threshold (default {DEFAULT_AMBIGUOUS_THRESHOLD})",
    )
    args = parser.parse_args()

    ok, errors = check_graph_integrity(args.graph, args.threshold)
    if not ok:
        print("graph integrity check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("graph integrity check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
