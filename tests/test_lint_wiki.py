from pathlib import Path

from semi_design_wiki.lint_wiki import LintReport, lint_wiki
from semi_design_wiki.sync_index import sync_index


def _ok_fm(type_: str = "architecture") -> dict:
    return {"type": type_, "tags": ["x"], "confidence": "high"}


def test_lint_clean_wiki(initialized_wiki: Path, make_page):
    make_page(initialized_wiki, "Alpha", _ok_fm(), "See [[Beta]].\n")
    make_page(initialized_wiki, "Beta", _ok_fm(), "")
    sync_index(initialized_wiki)

    report = lint_wiki(initialized_wiki)
    assert report.is_clean(), f"expected clean, got {report}"


def test_lint_detects_broken_link(initialized_wiki: Path, make_page):
    make_page(initialized_wiki, "Alpha", _ok_fm(), "See [[NonExistent]].\n")
    sync_index(initialized_wiki)

    report = lint_wiki(initialized_wiki)
    assert not report.is_clean()
    assert any(b.source == "Alpha" and b.target == "NonExistent" for b in report.broken_links)


def test_lint_detects_orphan(initialized_wiki: Path, make_page):
    make_page(initialized_wiki, "Lonely", _ok_fm(), "")
    # index.md 수동 덮어쓰기 — Lonely 링크 없음
    (initialized_wiki / "index.md").write_text("# Index\n\n(stub)\n")

    report = lint_wiki(initialized_wiki)
    assert "Lonely" in report.orphans


def test_lint_detects_missing_frontmatter(initialized_wiki: Path, make_page):
    make_page(initialized_wiki, "Incomplete", {"type": "architecture"}, "")
    sync_index(initialized_wiki)

    report = lint_wiki(initialized_wiki)
    assert "Incomplete" in [m.page for m in report.missing_fields]


def test_lint_flags_low_confidence(initialized_wiki: Path, make_page):
    make_page(
        initialized_wiki,
        "Shaky",
        {"type": "decision", "tags": [], "confidence": "low"},
        "",
    )
    sync_index(initialized_wiki)

    report = lint_wiki(initialized_wiki)
    assert "Shaky" in report.low_confidence


def test_lint_report_counts(initialized_wiki: Path, make_page):
    make_page(initialized_wiki, "A", _ok_fm(), "[[Ghost]]\n")
    make_page(initialized_wiki, "B", {"type": "error"}, "")  # missing tags+conf
    sync_index(initialized_wiki)

    report = lint_wiki(initialized_wiki)
    assert report.total_issues() == len(report.broken_links) + len(report.orphans) + len(
        report.missing_fields
    ) + len(report.low_confidence)


def test_report_is_clean_when_empty():
    r = LintReport()
    assert r.is_clean()
    assert r.total_issues() == 0
