from pathlib import Path

from semi_design_wiki.init_wiki import init_wiki
from semi_design_wiki.lint_wiki import lint_wiki
from semi_design_wiki.sync_index import sync_index


def test_full_workflow(tmp_path: Path):
    root = tmp_path / "wiki"
    init_wiki(root)

    (root / "Gemmini-Parameters.md").write_text(
        "---\n"
        "type: architecture\n"
        "tags: [gemmini, systolic]\n"
        "confidence: high\n"
        "---\n"
        "# Gemmini Parameters\n"
        "See also [[Dataflow-Types-WS-OS-IS]].\n"
    )
    (root / "Dataflow-Types-WS-OS-IS.md").write_text(
        "---\n"
        "type: architecture\n"
        "tags: [dataflow]\n"
        "confidence: medium\n"
        "---\n"
        "# Dataflow types\n"
    )

    sync_index(root)
    index_text = (root / "index.md").read_text()
    assert "[[Gemmini-Parameters]]" in index_text
    assert "[[Dataflow-Types-WS-OS-IS]]" in index_text

    report = lint_wiki(root)
    assert report.is_clean(), report.to_dict()
