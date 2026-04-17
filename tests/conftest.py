"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def wiki_root(tmp_path: Path) -> Path:
    """Empty directory intended to become a wiki root."""
    return tmp_path


@pytest.fixture
def initialized_wiki(tmp_path: Path) -> Path:
    """Pre-populated wiki tree for sync/lint tests."""
    root = tmp_path / "wiki"
    (root / "raw").mkdir(parents=True)
    (root / "raw" / "papers").mkdir()
    (root / "raw" / "manuals").mkdir()
    (root / "raw" / "pdk").mkdir()
    (root / "raw" / "benchmarks").mkdir()
    (root / "raw" / "sessions").mkdir()
    (root / "CLAUDE.md").write_text("# Wiki schema\n")
    (root / "index.md").write_text("# Index\n")
    (root / "log.md").write_text("# Ingest log\n")
    return root


def _page(root: Path, name: str, fm: dict, body: str = "") -> Path:
    """Helper to write a page file."""
    import yaml

    path = root / f"{name}.md"
    fm_text = yaml.safe_dump(fm, sort_keys=False).strip()
    path.write_text(f"---\n{fm_text}\n---\n{body}")
    return path


@pytest.fixture
def make_page():
    return _page
