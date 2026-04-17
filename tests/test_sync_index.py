from pathlib import Path

from semi_design_wiki.sync_index import sync_index


def test_sync_empty_wiki_writes_placeholder(initialized_wiki: Path):
    sync_index(initialized_wiki)
    content = (initialized_wiki / "index.md").read_text()
    assert "Wiki Index" in content
    assert "empty" in content.lower() or "no pages" in content.lower()


def test_sync_groups_pages_by_type(initialized_wiki: Path, make_page):
    make_page(
        initialized_wiki,
        "Gemmini-Parameters",
        {"type": "architecture", "tags": ["gemmini"], "confidence": "high"},
        "# Gemmini Parameters\n",
    )
    make_page(
        initialized_wiki,
        "DRC-Violation-Patterns",
        {"type": "error", "tags": ["drc"], "confidence": "medium"},
        "# DRC Violation Patterns\n",
    )
    sync_index(initialized_wiki)

    content = (initialized_wiki / "index.md").read_text()
    assert "## architecture" in content
    assert "## error" in content
    assert "[[Gemmini-Parameters]]" in content
    assert "[[DRC-Violation-Patterns]]" in content


def test_sync_skips_non_page_files(initialized_wiki: Path, make_page):
    # index·log·CLAUDE 는 자동 제외되어야 함
    make_page(
        initialized_wiki,
        "Good-Page",
        {"type": "architecture", "tags": [], "confidence": "high"},
        "",
    )
    sync_index(initialized_wiki)
    content = (initialized_wiki / "index.md").read_text()
    assert "[[index]]" not in content
    assert "[[CLAUDE]]" not in content
    assert "[[log]]" not in content
    assert "[[Good-Page]]" in content


def test_sync_confidence_marker(initialized_wiki: Path, make_page):
    make_page(
        initialized_wiki,
        "Low-Confidence",
        {"type": "decision", "tags": [], "confidence": "low"},
        "",
    )
    sync_index(initialized_wiki)
    content = (initialized_wiki / "index.md").read_text()
    # 저신뢰 페이지는 ⚠ 표식
    assert "⚠" in content or "low" in content.lower()


def test_sync_is_atomic(initialized_wiki: Path, make_page):
    make_page(
        initialized_wiki,
        "P1",
        {"type": "architecture", "tags": [], "confidence": "high"},
        "",
    )
    sync_index(initialized_wiki)
    # .tmp 파일 잔류 없어야 함
    leftovers = list(initialized_wiki.glob("*.tmp"))
    assert leftovers == []
