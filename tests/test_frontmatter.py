from pathlib import Path

import pytest

from semi_design_wiki.frontmatter import (
    MissingFieldsError,
    parse_file,
    validate_required,
)


def test_parse_file_with_frontmatter(tmp_path: Path):
    p = tmp_path / "page.md"
    p.write_text(
        "---\n"
        "type: architecture\n"
        "tags: [gemmini, systolic]\n"
        "confidence: high\n"
        "---\n"
        "# Gemmini Parameters\n"
        "Body text.\n"
    )
    fm, body = parse_file(p)
    assert fm["type"] == "architecture"
    assert fm["tags"] == ["gemmini", "systolic"]
    assert fm["confidence"] == "high"
    assert body.startswith("# Gemmini Parameters")


def test_parse_file_without_frontmatter(tmp_path: Path):
    p = tmp_path / "plain.md"
    p.write_text("# Just a heading\n")
    fm, body = parse_file(p)
    assert fm == {}
    assert body == "# Just a heading\n"


def test_parse_file_empty(tmp_path: Path):
    p = tmp_path / "empty.md"
    p.write_text("")
    fm, body = parse_file(p)
    assert fm == {}
    assert body == ""


def test_parse_file_malformed_frontmatter(tmp_path: Path):
    """닫는 --- 가 없으면 프론트매터 없음으로 취급"""
    p = tmp_path / "bad.md"
    p.write_text("---\ntype: foo\nbody text\n")
    fm, body = parse_file(p)
    assert fm == {}


def test_validate_required_ok():
    validate_required({"type": "arch", "tags": []}, ["type", "tags"])


def test_validate_required_missing():
    with pytest.raises(MissingFieldsError) as exc:
        validate_required({"type": "arch"}, ["type", "tags", "confidence"])
    assert "tags" in str(exc.value)
    assert "confidence" in str(exc.value)
