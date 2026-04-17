from pathlib import Path

from semi_design_wiki.init_wiki import init_wiki


EXPECTED_SUBDIRS = {"raw/papers", "raw/manuals", "raw/pdk", "raw/benchmarks", "raw/sessions"}
EXPECTED_FILES = {"index.md", "log.md", "CLAUDE.md"}


def test_init_creates_subdirs(wiki_root: Path):
    init_wiki(wiki_root)
    for sub in EXPECTED_SUBDIRS:
        assert (wiki_root / sub).is_dir(), f"missing {sub}"


def test_init_creates_top_files(wiki_root: Path):
    init_wiki(wiki_root)
    for f in EXPECTED_FILES:
        assert (wiki_root / f).is_file(), f"missing {f}"


def test_init_is_idempotent(wiki_root: Path):
    init_wiki(wiki_root)
    index = wiki_root / "index.md"
    index.write_text("# Customized\n")
    init_wiki(wiki_root)
    assert index.read_text() == "# Customized\n", "idempotent call should not overwrite"


def test_init_creates_claude_md_with_schema(wiki_root: Path):
    init_wiki(wiki_root)
    content = (wiki_root / "CLAUDE.md").read_text()
    assert "frontmatter" in content.lower()
    assert "wiki-link" in content.lower() or "[[" in content
