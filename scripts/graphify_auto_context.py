"""UserPromptSubmit hook entry - injects relevant subgraph into Claude Code context.

Invoked by the hook registered in .claude/settings.json:
    uv run python scripts/graphify_auto_context.py "<user prompt>"

Always exits 0. A missing or broken graph must never block the user's prompt.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

_OPEN_TAG = "<graphify-context>"
_CLOSE_TAG = "</graphify-context>"
_DEFAULT_GRAPH = "graphify-out/graph.json"
_DEFAULT_BUDGET = 800
_DEFAULT_DEPTH = 2
_MIN_WORDS = 3


def _read_prompt() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def _extract_terms(prompt: str) -> list[str]:
    return [t.lower() for t in prompt.split() if len(t) > 2]


def build_context(
    prompt: str,
    graph_path: Path = Path(_DEFAULT_GRAPH),
    token_budget: int = _DEFAULT_BUDGET,
    depth: int = _DEFAULT_DEPTH,
) -> str:
    if not graph_path.exists():
        return ""

    words = prompt.split()
    if len(words) < _MIN_WORDS:
        return ""

    try:
        from graphify.serve import _score_nodes, _bfs, _subgraph_to_text
        from networkx.readwrite import json_graph
    except ImportError:
        return ""

    try:
        data = json.loads(graph_path.read_text())
        G = json_graph.node_link_graph(data, edges="links")
    except (json.JSONDecodeError, OSError, KeyError) as exc:
        print(f"[graphify auto_context] graph load failed: {exc}", file=sys.stderr)
        return ""

    terms = _extract_terms(prompt)
    if not terms:
        return ""

    scored = _score_nodes(G, terms)
    start_nodes = [nid for _, nid in scored[:3]]
    if not start_nodes:
        return ""

    nodes, edges = _bfs(G, start_nodes, depth)
    body = _subgraph_to_text(G, nodes, edges, token_budget)
    if not body.strip():
        return ""

    seeds = [G.nodes[n].get("label", n) for n in start_nodes]
    header = f"Relevant nodes from graphify knowledge graph (seeds: {', '.join(seeds)}):"
    return f"{_OPEN_TAG}\n{header}\n{body}\n{_CLOSE_TAG}"


def main() -> int:
    prompt = _read_prompt()
    if not prompt.strip():
        return 0
    try:
        block = build_context(prompt)
    except Exception as exc:
        print(f"[graphify auto_context] unexpected error: {exc}", file=sys.stderr)
        return 0
    if block:
        print(block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
