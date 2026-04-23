"""Console-script entry point for `semi-confidence`.

Thin wrapper around `semi_design_runner.confidence.main` so pyproject.toml can
expose the CLI as a packaged console script. All logic (§3.2 mapping, §3.3 #4
source-identity exclusion, BFS source_count) lives in `confidence.py`.
"""

from __future__ import annotations

import sys

from semi_design_runner.confidence import main as _compute_main


def main() -> None:
    """CLI entry point. Forwards argv and exits with the returned code."""
    sys.exit(_compute_main())


if __name__ == "__main__":
    main()
