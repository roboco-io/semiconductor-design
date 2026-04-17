"""Health checks for the wiki: broken links, orphans, missing fields, low confidence."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click

from .frontmatter import parse_file
from .sync_index import EXCLUDED_STEMS

WIKI_LINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")
REQUIRED_FIELDS = ("type", "tags", "confidence")


@dataclass
class BrokenLink:
    source: str
    target: str


@dataclass
class MissingFieldEntry:
    page: str
    missing: list[str]


@dataclass
class LintReport:
    broken_links: list[BrokenLink] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    missing_fields: list[MissingFieldEntry] = field(default_factory=list)
    low_confidence: list[str] = field(default_factory=list)

    def total_issues(self) -> int:
        return (
            len(self.broken_links)
            + len(self.orphans)
            + len(self.missing_fields)
            + len(self.low_confidence)
        )

    def is_clean(self) -> bool:
        return self.total_issues() == 0

    def to_dict(self) -> dict:
        return {
            "broken_links": [{"source": b.source, "target": b.target} for b in self.broken_links],
            "orphans": self.orphans,
            "missing_fields": [{"page": m.page, "missing": m.missing} for m in self.missing_fields],
            "low_confidence": self.low_confidence,
            "total_issues": self.total_issues(),
        }


def lint_wiki(root: Path) -> LintReport:
    """Run all checks and return the aggregated report."""
    pages = _list_pages(root)
    page_names = {p.stem for p in pages}
    report = LintReport()

    for path in pages:
        fm, body = parse_file(path)
        _check_broken_links(path, body, page_names, report)
        _check_missing_fields(path, fm, report)
        _check_low_confidence(path, fm, report)

    _check_orphans(root, page_names, report)
    return report


def _list_pages(root: Path) -> list[Path]:
    return [p for p in sorted(root.glob("*.md")) if p.stem not in EXCLUDED_STEMS]


def _check_broken_links(path: Path, body: str, names: set[str], report: LintReport) -> None:
    for match in WIKI_LINK_RE.finditer(body):
        target = match.group(1).strip()
        if target not in names:
            report.broken_links.append(BrokenLink(source=path.stem, target=target))


def _check_missing_fields(path: Path, fm: dict, report: LintReport) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in fm]
    if missing:
        report.missing_fields.append(MissingFieldEntry(page=path.stem, missing=missing))


def _check_low_confidence(path: Path, fm: dict, report: LintReport) -> None:
    if fm.get("confidence") == "low":
        report.low_confidence.append(path.stem)


def _check_orphans(root: Path, page_names: set[str], report: LintReport) -> None:
    index_path = root / "index.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    linked = {m.group(1).strip() for m in WIKI_LINK_RE.finditer(index_text)}
    report.orphans = sorted(page_names - linked)


@click.command()
@click.option("--root", type=click.Path(path_type=Path), default=Path("wiki"))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def main(root: Path, fmt: str) -> None:
    """CLI: run lint and exit 0 if clean, 1 otherwise."""
    report = lint_wiki(root)
    if fmt == "json":
        click.echo(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_text(report)
    sys.exit(0 if report.is_clean() else 1)


def _print_text(report: LintReport) -> None:
    if report.is_clean():
        click.echo("✓ wiki is clean")
        return
    if report.broken_links:
        click.echo(f"✗ {len(report.broken_links)} broken link(s):")
        for b in report.broken_links:
            click.echo(f"    {b.source} → [[{b.target}]]")
    if report.orphans:
        click.echo(f"✗ {len(report.orphans)} orphan page(s) not in index:")
        for o in report.orphans:
            click.echo(f"    {o}")
    if report.missing_fields:
        click.echo(f"✗ {len(report.missing_fields)} page(s) with missing frontmatter:")
        for m in report.missing_fields:
            click.echo(f"    {m.page}: missing {', '.join(m.missing)}")
    if report.low_confidence:
        click.echo(f"⚠ {len(report.low_confidence)} low-confidence page(s):")
        for n in report.low_confidence:
            click.echo(f"    {n}")
