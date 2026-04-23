"""Inject L2 freshness metadata into a graphify-produced graph.json.

Post-`/graphify --update` (or `/graphify .` full rebuild) hook that materialises
the per-node freshness fields defined by L2 derived spec §4.1:

    last_ingested — ISO-8601 mtime of source .md file(s). Refreshed every run.
    valid_from    — ISO-8601 first-seen timestamp. Preserved after first ingest.
    valid_to      — ISO-8601 invalidation timestamp (default None).
                    Preserved on every run; manual override supported.

**Field placement**: a top-level ``freshness`` dict on each node. graphify v0.4.25
emits nodes as flat dicts (keys: ``id``, ``label``, ``source_file``, ``community``,
``norm_label``, ``file_type``, ``source_location``) with no ``attributes`` or
``metadata`` container. Injecting a nested dict keeps downstream consumers
(`L2.memory.recall` → `L2RecallNode`) able to pluck a single key without
touching unrelated fields.

**What this hook does NOT write**: ``age_days``. Spec §4.2 states the derived
integer is the consumer's (L1/L3) responsibility, because a writeback would go
stale between runs. Callers compute ``age_days = (now - last_ingested).days``.

**Idempotency**: re-running this script with unchanged file mtimes is a no-op
(last_ingested regenerates from mtime deterministically, valid_from/valid_to
are always preserved). Atomic write via ``graph.json.tmp`` + ``os.replace``.

**Source-file resolution**: the script reads ``node["source_file"]`` (single
path string) and optionally ``node["source_files"]`` (list of paths). Paths are
resolved relative to ``--corpus-root`` (default: current working directory).
When multiple sources exist, ``last_ingested`` = max(mtime of each existing
file). Non-existent source files are skipped; if ALL sources are unresolvable,
fields are set to ``None`` and the node id is written to stderr as
``[WARN] <id>: ...``.

Exit code: 0 on success, 1 on malformed graph.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _mtime_iso(path: Path) -> str:
    """Return ISO-8601 UTC timestamp of ``path`` mtime (timezone-aware)."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _resolve_source_paths(node: dict, corpus_root: Path) -> list[Path]:
    """Collect all source-file candidates declared on ``node``.

    Accepts both ``source_file`` (single string) and ``source_files`` (list).
    Duplicate paths are deduplicated while preserving order.
    """
    candidates: list[str] = []
    single = node.get("source_file")
    if isinstance(single, str) and single:
        candidates.append(single)
    multi = node.get("source_files")
    if isinstance(multi, list):
        for item in multi:
            if isinstance(item, str) and item and item not in candidates:
                candidates.append(item)
    return [corpus_root / c for c in candidates]


def _compute_last_ingested(
    source_paths: list[Path],
) -> tuple[Optional[str], list[Path]]:
    """Return (ISO-8601 last_ingested or None, list of missing paths).

    last_ingested = ISO-8601 of the max mtime across all EXISTING source files.
    If none of the candidates exist on disk, returns (None, all-candidates).
    """
    existing = [p for p in source_paths if p.exists() and p.is_file()]
    missing = [p for p in source_paths if p not in existing]
    if not existing:
        return None, missing
    newest = max(existing, key=lambda p: p.stat().st_mtime)
    return _mtime_iso(newest), missing


def _merge_freshness(existing: dict, last_ingested: Optional[str]) -> dict:
    """Combine new last_ingested with preserved valid_from / valid_to."""
    prev_valid_from = existing.get("valid_from") if isinstance(existing, dict) else None
    prev_valid_to = existing.get("valid_to") if isinstance(existing, dict) else None

    # valid_from: set on first ingest, preserved thereafter.
    if prev_valid_from is not None:
        valid_from = prev_valid_from
    else:
        valid_from = last_ingested  # may be None if source missing

    # valid_to: always preserved (None → None, set → set)
    return {
        "last_ingested": last_ingested,
        "valid_from": valid_from,
        "valid_to": prev_valid_to,
    }


def inject_freshness(graph_path: Path, corpus_root: Path) -> int:
    """Inject/refresh ``freshness`` dict on every node of graph_path.

    Returns number of nodes flagged with a warning (unresolvable source_file).
    """
    graph = json.loads(graph_path.read_text())
    nodes = graph.get("nodes") or []
    warnings = 0

    for node in nodes:
        source_paths = _resolve_source_paths(node, corpus_root)
        last_ingested, missing = _compute_last_ingested(source_paths)
        existing = node.get("freshness") or {}

        if last_ingested is None:
            # No resolvable source → fields all None; emit stderr warning.
            node_id = node.get("id", "<unknown>")
            missing_str = ", ".join(str(p) for p in missing) or "<no source_file>"
            print(
                f"[WARN] {node_id}: no resolvable source_file ({missing_str})",
                file=sys.stderr,
            )
            warnings += 1
            node["freshness"] = {
                "last_ingested": None,
                "valid_from": existing.get("valid_from"),
                "valid_to": existing.get("valid_to"),
            }
        else:
            node["freshness"] = _merge_freshness(existing, last_ingested)

    # Atomic write: tmp → rename.
    tmp_path = graph_path.with_suffix(graph_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    os.replace(tmp_path, graph_path)
    return warnings


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path("graphify-out/graph.json"),
        help="Path to graphify-produced graph.json (default: graphify-out/graph.json)",
    )
    parser.add_argument(
        "--corpus-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory for resolving relative source_file paths (default: cwd)",
    )
    # Positional alias for backward-compatible shell pipelines.
    parser.add_argument(
        "graph_positional",
        nargs="?",
        type=Path,
        default=None,
        help="Optional positional graph.json (overrides --graph if given)",
    )
    args = parser.parse_args(argv)

    graph_path = args.graph_positional or args.graph
    try:
        inject_freshness(graph_path, corpus_root=args.corpus_root)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"inject_freshness FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"inject_freshness OK: {graph_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
