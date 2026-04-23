"""CLI entry for L2 Alternative B confidence computation (L2 spec §3.2).

Thin wrapper over `semi_design_runner.confidence` so the script runs
unchanged as `python -m scripts.compute_confidence` (dev) while the packaged
console script `semi-confidence` imports the same logic from the wheel.

Core algorithm + mapping table documentation live in
`src/semi_design_runner/confidence.py`. §3.3 #4 (source identity required) and
AMBIGUOUS→None enforcement are implemented there and covered by
`tests/runner/test_compute_confidence.py`.

Usage:
    python -m scripts.compute_confidence --graph graphify-out/graph.json --all
    python -m scripts.compute_confidence --graph graphify-out/graph.json --node <id>
"""

from __future__ import annotations

import sys

from semi_design_runner.confidence import (
    compute_all_confidence,
    compute_node_confidence,
    main,
)

__all__ = ["compute_all_confidence", "compute_node_confidence", "main"]


if __name__ == "__main__":
    sys.exit(main())
