from pathlib import Path

from click.testing import CliRunner

from semi_design_wiki.init_wiki import init_wiki
from semi_design_wiki.init_wiki import main as init_main
from semi_design_wiki.lint_wiki import lint_wiki
from semi_design_wiki.lint_wiki import main as lint_main
from semi_design_wiki.sync_index import main as sync_main
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
        "---\ntype: architecture\ntags: [dataflow]\nconfidence: medium\n---\n# Dataflow types\n"
    )

    sync_index(root)
    index_text = (root / "index.md").read_text()
    assert "[[Gemmini-Parameters]]" in index_text
    assert "[[Dataflow-Types-WS-OS-IS]]" in index_text

    report = lint_wiki(root)
    assert report.is_clean(), report.to_dict()


def test_full_workflow_via_cli(tmp_path: Path):
    runner = CliRunner()

    clean_root = tmp_path / "clean-wiki"

    init_result = runner.invoke(init_main, ["--root", str(clean_root)], catch_exceptions=False)
    assert init_result.exit_code == 0, init_result.output
    assert clean_root.is_dir()
    assert (clean_root / "index.md").exists()

    (clean_root / "Gemmini-Parameters.md").write_text(
        "---\n"
        "type: architecture\n"
        "tags: [gemmini, systolic]\n"
        "confidence: high\n"
        "---\n"
        "# Gemmini Parameters\n"
        "See also [[Dataflow-Types-WS-OS-IS]].\n"
    )
    (clean_root / "Dataflow-Types-WS-OS-IS.md").write_text(
        "---\ntype: architecture\ntags: [dataflow]\nconfidence: medium\n---\n# Dataflow types\n"
    )

    sync_result = runner.invoke(sync_main, ["--root", str(clean_root)], catch_exceptions=False)
    assert sync_result.exit_code == 0, sync_result.output
    index_text = (clean_root / "index.md").read_text()
    assert "[[Gemmini-Parameters]]" in index_text
    assert "[[Dataflow-Types-WS-OS-IS]]" in index_text

    lint_clean = runner.invoke(
        lint_main,
        ["--root", str(clean_root), "--format", "text"],
        catch_exceptions=False,
    )
    assert lint_clean.exit_code == 0, lint_clean.output
    assert "✓ wiki is clean" in lint_clean.output

    lint_clean_json = runner.invoke(
        lint_main,
        ["--root", str(clean_root), "--format", "json"],
        catch_exceptions=False,
    )
    assert lint_clean_json.exit_code == 0, lint_clean_json.output
    assert '"total_issues": 0' in lint_clean_json.output

    broken_root = tmp_path / "broken-wiki"
    init_wiki(broken_root)
    (broken_root / "Has-Broken-Link.md").write_text(
        "---\n"
        "type: architecture\n"
        "tags: [broken]\n"
        "confidence: high\n"
        "---\n"
        "# Broken\n"
        "Refers to [[NonExistent]].\n"
    )
    sync_index(broken_root)

    lint_broken = runner.invoke(
        lint_main,
        ["--root", str(broken_root), "--format", "text"],
        catch_exceptions=False,
    )
    assert lint_broken.exit_code == 1
    assert "broken link" in lint_broken.output
