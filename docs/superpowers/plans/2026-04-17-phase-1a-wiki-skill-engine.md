# Phase 1a — Wiki Skill Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `semi-design-wiki` 스킬의 결정론적 엔진(`init_wiki.py`, `sync_index.py`, `lint_wiki.py`)을 TDD로 구현해, 이후 Phase 1b·1c가 의존할 위키 관리 도구를 완성한다.

**Architecture:** Python 3.12 + `uv` 프로젝트. 세 스크립트는 각각 stdlib만 사용(외부 의존성 최소). `wiki/` 디렉토리 구조는 Karpathy LLM Wiki 패턴을 따르며, 프론트매터는 YAML. 스킬은 프로젝트 로컬 `.claude/skills/semi-design-wiki/`에 위치.

**Tech Stack:** Python 3.12, uv, pytest, PyYAML, click, stdlib(re·pathlib·json).

---

## File Structure

```
semiconductor-design/
├── pyproject.toml                         # uv 프로젝트 메타
├── uv.lock                                # 잠금 파일
├── Makefile                               # 단축 명령
├── src/
│   └── semi_design_wiki/
│       ├── __init__.py
│       ├── frontmatter.py                 # YAML 프론트매터 파싱·검증
│       ├── init_wiki.py                   # 디렉토리 초기화
│       ├── sync_index.py                  # wiki/*.md 스캔 → index.md 생성
│       └── lint_wiki.py                   # 끊어진 링크·고아·저신뢰 점검
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # pytest 픽스처(tmp 위키 트리)
│   ├── test_frontmatter.py
│   ├── test_init_wiki.py
│   ├── test_sync_index.py
│   └── test_lint_wiki.py
└── .claude/
    └── skills/
        └── semi-design-wiki/
            └── scripts/                   # 위 스크립트들의 CLI 래퍼(심볼릭 링크 또는 entry point 호출)
```

**경계 원칙**: 세 스크립트는 각각 한 책임. `frontmatter.py`만 공통 유틸로 공유. 테스트는 픽스처에서 실제 `tmp_path`에 파일 생성 후 함수 호출.

---

## Task 1: 프로젝트 스캐폴딩 (uv + pytest 동작)

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `src/semi_design_wiki/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_sanity.py`

- [ ] **Step 1: `pyproject.toml` 작성**

```toml
[project]
name = "semi-design-wiki"
version = "0.1.0"
description = "Semiconductor design domain wiki engine"
requires-python = ">=3.12"
dependencies = [
    "pyyaml>=6.0",
    "click>=8.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.6",
]

[project.scripts]
wiki-init = "semi_design_wiki.init_wiki:main"
wiki-sync = "semi_design_wiki.sync_index:main"
wiki-lint = "semi_design_wiki.lint_wiki:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/semi_design_wiki"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: `Makefile` 작성**

```makefile
.PHONY: install test lint fmt clean

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

clean:
	rm -rf .pytest_cache .ruff_cache dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

- [ ] **Step 3: 빈 패키지 파일**

Create `src/semi_design_wiki/__init__.py`:
```python
"""Semiconductor design domain wiki engine."""

__version__ = "0.1.0"
```

Create `tests/__init__.py`:
```python
```

- [ ] **Step 4: sanity test 작성**

Create `tests/test_sanity.py`:
```python
from semi_design_wiki import __version__


def test_version():
    assert __version__ == "0.1.0"
```

- [ ] **Step 5: uv 설치 및 테스트 실행**

```bash
uv sync --all-extras
uv run pytest -v
```

Expected: `1 passed`

- [ ] **Step 6: 커밋**

```bash
git add pyproject.toml uv.lock Makefile src/ tests/
git commit -m "chore: scaffold uv project with pytest baseline"
```

---

## Task 2: Frontmatter 파서 (공통 유틸)

**Files:**
- Create: `src/semi_design_wiki/frontmatter.py`
- Create: `tests/test_frontmatter.py`

페이지 파일의 YAML 프론트매터를 파싱한다. 스펙:
- 파일이 `---\n<yaml>\n---\n<body>` 형식이면 `(dict, body)` 반환
- 프론트매터 없으면 `({}, 전체 파일)`
- 필수 필드 검증 함수 별도 제공(`validate_required(fm, fields)`)

- [ ] **Step 1: 테스트 작성**

Create `tests/test_frontmatter.py`:
```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest tests/test_frontmatter.py -v
```

Expected: `ModuleNotFoundError: No module named 'semi_design_wiki.frontmatter'`

- [ ] **Step 3: 구현**

Create `src/semi_design_wiki/frontmatter.py`:
```python
"""YAML frontmatter parsing for wiki pages."""

from __future__ import annotations

from pathlib import Path

import yaml


class MissingFieldsError(ValueError):
    """Raised when required frontmatter fields are missing."""


def parse_file(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Empty dict if no frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        return {}, text
    return data, body


def validate_required(fm: dict, fields: list[str]) -> None:
    """Raise MissingFieldsError if any required field is missing."""
    missing = [f for f in fields if f not in fm]
    if missing:
        raise MissingFieldsError(f"missing required fields: {', '.join(missing)}")
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest tests/test_frontmatter.py -v
```

Expected: `6 passed`

- [ ] **Step 5: 커밋**

```bash
git add src/semi_design_wiki/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: add yaml frontmatter parser with field validation"
```

---

## Task 3: conftest 공용 픽스처

**Files:**
- Create: `tests/conftest.py`

여러 테스트에서 공통으로 쓸 임시 wiki 트리 픽스처.

- [ ] **Step 1: 픽스처 작성**

Create `tests/conftest.py`:
```python
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
```

- [ ] **Step 2: 커밋** (아직 테스트 추가 전)

```bash
git add tests/conftest.py
git commit -m "test: add shared wiki fixtures"
```

---

## Task 4: `init_wiki.py` — 위키 디렉토리 초기화

**Files:**
- Create: `src/semi_design_wiki/init_wiki.py`
- Create: `tests/test_init_wiki.py`

**스펙**:
- `init_wiki(root: Path)` 호출 시:
  - `{root}/raw/{papers,manuals,pdk,benchmarks,sessions}/` 생성
  - `{root}/index.md`, `{root}/log.md`, `{root}/CLAUDE.md` 생성 (없을 때만)
- 재호출 시 멱등 — 기존 파일 덮어쓰지 않음
- CLI: `wiki-init --root wiki/` (기본 `wiki`)

- [ ] **Step 1: 테스트 작성**

Create `tests/test_init_wiki.py`:
```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest tests/test_init_wiki.py -v
```

Expected: `ModuleNotFoundError` 또는 `ImportError`

- [ ] **Step 3: 구현**

Create `src/semi_design_wiki/init_wiki.py`:
```python
"""Initialize wiki directory structure (idempotent)."""

from __future__ import annotations

from pathlib import Path

import click

SUBDIRS = ("raw/papers", "raw/manuals", "raw/pdk", "raw/benchmarks", "raw/sessions")

CLAUDE_MD_TEMPLATE = """# Wiki Schema

This directory follows the Karpathy LLM Wiki pattern.

## Directory layout

- `raw/` — immutable source documents (LLM reads only)
- `wiki/*.md` — compiled knowledge pages (LLM maintains)
- `index.md` — auto-generated index, regenerated by `wiki sync`
- `log.md` — append-only ingest history

## Page frontmatter

Every wiki page MUST have:

```yaml
---
type: architecture | flow | error | workload | decision
tags: [list, of, keywords]
confidence: high | medium | low
sources: [raw/papers/xxx.pdf, ...]
last_ingested: 2026-04-17
---
```

## Wiki-link format

Use `[[Page-Title]]` (Obsidian compatible). The file `wiki/Page-Title.md` resolves.
"""

INDEX_MD_TEMPLATE = """# Wiki Index

> This file is auto-generated by `wiki-sync`. Do not edit by hand.

(empty — run `wiki-sync` after adding pages)
"""

LOG_MD_TEMPLATE = """# Ingest Log

Append-only record of `wiki ingest` runs.
"""


def init_wiki(root: Path) -> None:
    """Create wiki directory structure if missing. Idempotent."""
    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)

    _ensure_file(root / "CLAUDE.md", CLAUDE_MD_TEMPLATE)
    _ensure_file(root / "index.md", INDEX_MD_TEMPLATE)
    _ensure_file(root / "log.md", LOG_MD_TEMPLATE)


def _ensure_file(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


@click.command()
@click.option("--root", type=click.Path(path_type=Path), default=Path("wiki"))
def main(root: Path) -> None:
    """CLI: initialize a wiki directory."""
    init_wiki(root)
    click.echo(f"Initialized wiki at {root}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest tests/test_init_wiki.py -v
```

Expected: `4 passed`

- [ ] **Step 5: CLI 동작 수동 확인**

```bash
uv run wiki-init --root /tmp/wiki-test
ls /tmp/wiki-test/raw
```

Expected: `benchmarks  manuals  papers  pdk  sessions`

정리:
```bash
rm -rf /tmp/wiki-test
```

- [ ] **Step 6: 커밋**

```bash
git add src/semi_design_wiki/init_wiki.py tests/test_init_wiki.py
git commit -m "feat: idempotent wiki directory initializer with cli"
```

---

## Task 5: `sync_index.py` — 인덱스 자동 재빌드

**Files:**
- Create: `src/semi_design_wiki/sync_index.py`
- Create: `tests/test_sync_index.py`

**스펙**:
- `wiki/` 아래 `*.md` 중 `index.md`·`log.md`·`CLAUDE.md` 제외하고 스캔
- 각 페이지의 프론트매터에서 `type`·`tags`·`confidence` 읽음
- `index.md`를 `type`별로 그룹핑된 리스트로 재생성
- 원자적 쓰기(`.tmp` 후 rename)로 중간 실패 방지

- [ ] **Step 1: 테스트 작성**

Create `tests/test_sync_index.py`:
```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest tests/test_sync_index.py -v
```

Expected: import 실패.

- [ ] **Step 3: 구현**

Create `src/semi_design_wiki/sync_index.py`:
```python
"""Scan wiki/ pages and regenerate index.md grouped by type."""

from __future__ import annotations

from pathlib import Path

import click

from .frontmatter import parse_file

EXCLUDED_STEMS = {"index", "log", "CLAUDE"}
HEADER = "# Wiki Index\n\n> Auto-generated by `wiki-sync`. Do not edit by hand.\n\n"
EMPTY_MARKER = "(no pages yet — run `wiki-ingest` to add content)\n"


def sync_index(root: Path) -> None:
    """Rewrite {root}/index.md atomically based on page frontmatter."""
    pages = _collect_pages(root)
    content = _render_index(pages)
    _atomic_write(root / "index.md", content)


def _collect_pages(root: Path) -> list[dict]:
    """Return list of {name, type, tags, confidence} for every valid page."""
    entries: list[dict] = []
    for path in sorted(root.glob("*.md")):
        if path.stem in EXCLUDED_STEMS:
            continue
        fm, _body = parse_file(path)
        entries.append(
            {
                "name": path.stem,
                "type": fm.get("type", "uncategorized"),
                "tags": fm.get("tags", []) or [],
                "confidence": fm.get("confidence", "unknown"),
            }
        )
    return entries


def _render_index(pages: list[dict]) -> str:
    if not pages:
        return HEADER + EMPTY_MARKER
    grouped: dict[str, list[dict]] = {}
    for p in pages:
        grouped.setdefault(p["type"], []).append(p)
    parts = [HEADER]
    for type_name in sorted(grouped):
        parts.append(f"## {type_name}\n\n")
        for p in sorted(grouped[type_name], key=lambda x: x["name"]):
            marker = " ⚠ low-confidence" if p["confidence"] == "low" else ""
            tag_part = f" _(tags: {', '.join(p['tags'])})_" if p["tags"] else ""
            parts.append(f"- [[{p['name']}]]{marker}{tag_part}\n")
        parts.append("\n")
    return "".join(parts)


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


@click.command()
@click.option("--root", type=click.Path(path_type=Path), default=Path("wiki"))
def main(root: Path) -> None:
    """CLI: regenerate index.md from wiki pages."""
    sync_index(root)
    click.echo(f"Synced index for {root}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest tests/test_sync_index.py -v
```

Expected: `5 passed`

- [ ] **Step 5: 전체 테스트 재실행 (회귀 확인)**

```bash
uv run pytest -v
```

Expected: `16 passed` (sanity 1 + frontmatter 6 + init 4 + sync 5)

- [ ] **Step 6: 커밋**

```bash
git add src/semi_design_wiki/sync_index.py tests/test_sync_index.py
git commit -m "feat: atomic index rebuilder grouped by page type"
```

---

## Task 6: `lint_wiki.py` — 건강 점검

**Files:**
- Create: `src/semi_design_wiki/lint_wiki.py`
- Create: `tests/test_lint_wiki.py`

**스펙**: 4가지 검사를 수행하고 `LintReport` 반환.
1. **Broken links**: 페이지 내 `[[Name]]` 중 `Name.md`가 존재하지 않는 것
2. **Orphans**: `index.md`에 등장하지 않는 페이지(sync 후에도 남으면 경고)
3. **Missing frontmatter**: `type`·`tags`·`confidence` 중 하나라도 빠진 페이지
4. **Low confidence**: `confidence: low` 페이지 목록

CLI는 종료 코드 0 = clean, 1 = 문제 있음. `--format json|text`.

- [ ] **Step 1: 테스트 작성**

Create `tests/test_lint_wiki.py`:
```python
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
uv run pytest tests/test_lint_wiki.py -v
```

Expected: import 실패.

- [ ] **Step 3: 구현**

Create `src/semi_design_wiki/lint_wiki.py`:
```python
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
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
uv run pytest tests/test_lint_wiki.py -v
```

Expected: `7 passed`

- [ ] **Step 5: 전체 테스트 실행 (회귀 확인)**

```bash
uv run pytest -v
```

Expected: `23 passed`

- [ ] **Step 6: CLI end-to-end 수동 확인**

```bash
rm -rf /tmp/wiki-demo && mkdir /tmp/wiki-demo
uv run wiki-init --root /tmp/wiki-demo
cat > /tmp/wiki-demo/Sample.md <<'EOF'
---
type: architecture
tags: [demo]
confidence: high
---
Links to [[Ghost]].
EOF
uv run wiki-sync --root /tmp/wiki-demo
uv run wiki-lint --root /tmp/wiki-demo --format text; echo "exit=$?"
rm -rf /tmp/wiki-demo
```

Expected: `✗ 1 broken link(s):` 및 `exit=1`.

- [ ] **Step 7: 커밋**

```bash
git add src/semi_design_wiki/lint_wiki.py tests/test_lint_wiki.py
git commit -m "feat: wiki lint with broken links, orphans, frontmatter, confidence checks"
```

---

## Task 7: 통합 smoke test — init → page → sync → lint

**Files:**
- Create: `tests/test_integration.py`

세 스크립트가 실제 워크플로우로 맞물리는지 검증.

- [ ] **Step 1: 통합 테스트 작성**

Create `tests/test_integration.py`:
```python
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
```

- [ ] **Step 2: 테스트 실행**

```bash
uv run pytest tests/test_integration.py -v
```

Expected: `1 passed`

- [ ] **Step 3: 전체 테스트 + coverage 확인**

```bash
uv run pytest --cov=semi_design_wiki --cov-report=term-missing
```

Expected: 모든 테스트 통과, coverage ≥ 85%

- [ ] **Step 4: 커밋**

```bash
git add tests/test_integration.py
git commit -m "test: end-to-end wiki workflow integration test"
```

---

## Task 8: `.claude/skills/semi-design-wiki/` 스킬 뼈대 연결

**Files:**
- Create: `.claude/skills/semi-design-wiki/SKILL.md`
- Create: `.claude/skills/semi-design-wiki/references/placeholder.md`

이 task는 Phase 1b에서 내용을 채울 공간 확보용 — 현재는 스킬 메타만 등록해 Claude Code가 인식하게 함.

- [ ] **Step 1: 디렉토리 생성 및 placeholder 작성**

```bash
mkdir -p .claude/skills/semi-design-wiki/references
mkdir -p .claude/skills/semi-design-wiki/scripts
```

- [ ] **Step 2: 스킬 정의 파일**

Create `.claude/skills/semi-design-wiki/SKILL.md`:
```markdown
---
name: semi-design-wiki
description: Semiconductor design domain wiki management - init / sync / lint / ingest / query. Triggers when user mentions wiki, page ingestion, domain knowledge for chip design. Full content of pages and ingest workflow is defined in references/ and filled in Phase 1b.
---

# semi-design-wiki

Phase 1a scaffolds the scripts (`wiki-init`, `wiki-sync`, `wiki-lint`).
Phase 1b will populate `references/page-templates.md`, `references/ingest-workflow.md`, `references/semiconductor-ontology.md`.

## Commands

- `wiki-init --root wiki` — create directory structure
- `wiki-sync --root wiki` — regenerate `wiki/index.md`
- `wiki-lint --root wiki` — health check (exit 1 on issues)

## Ingest / Query (Phase 1b)

Not yet implemented. See Phase 1b plan.
```

- [ ] **Step 3: placeholder reference**

Create `.claude/skills/semi-design-wiki/references/placeholder.md`:
```markdown
# References (to be filled in Phase 1b)

- `page-templates.md` — 6 page-type templates
- `ingest-workflow.md` — 5-step ingest procedure
- `semiconductor-ontology.md` — domain page taxonomy
```

- [ ] **Step 4: 커밋**

```bash
git add .claude/
git commit -m "chore: scaffold semi-design-wiki skill shell"
```

---

## Task 9: README 갱신 — Phase 1a 결과 기록

**Files:**
- Create: `README.md`

- [ ] **Step 1: README 작성**

Create `README.md`:
```markdown
# semiconductor-design

AI agent-driven deep learning accelerator design, targeting MLPerf Tiny
workloads on SkyWater sky130A via Chipyard/Gemmini + OpenLane2.

See [design spec](docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md)
for the full design rationale.

## Phase 1a — Wiki Skill Engine (done)

```bash
make install      # uv sync
make test         # pytest
uv run wiki-init --root wiki
uv run wiki-sync --root wiki
uv run wiki-lint --root wiki
```

## Next phases

| # | Sub-plan | Status |
|---|---|---|
| 1a | Wiki Skill Engine | ✅ done |
| 1b | Wiki Content Bootstrap | pending |
| 1c | Local EDA Smoke Tests | pending |
| 2 | AWS Foundation (CDK) | pending |
| 3 | Single-Candidate Flow | pending |
| 4 | Agent Orchestration | pending |
| 5 | Evolution Loop + Dashboard | pending |
| 6 | Baselines & Public Release | pending |

## Open decisions

Tracked in [issues/](issues/README.md).
```

- [ ] **Step 2: 커밋**

```bash
git add README.md
git commit -m "docs: add top-level readme with phase status"
```

---

## Completion Criteria

Phase 1a 종료 시:
- `make test` — 모든 테스트 통과 (약 24 tests)
- `uv run wiki-init --root /tmp/x && uv run wiki-sync --root /tmp/x && uv run wiki-lint --root /tmp/x` 순차 실행 가능
- 모든 스크립트 coverage ≥ 85%
- Git 히스토리에 Task별 커밋 10개 내외

---

## Self-Review Notes

- [x] 스펙 §8(Knowledge Substrate)의 "scripts/init.sh, sync_index.py, lint_wiki.py" 요구사항 → Task 4·5·6으로 커버
- [x] 스펙 §8.2의 페이지 프론트매터(type/tags/confidence/sources/last_ingested) → `frontmatter.py`가 검증, `REQUIRED_FIELDS`는 type/tags/confidence만 필수(sources/last_ingested는 옵셔널)
- [x] 멱등성 요구(§8.1) → Task 4 `test_init_is_idempotent`
- [x] 원자적 쓰기 → Task 5 `test_sync_is_atomic`
- [x] `[[wiki-link]]` 포맷 → Task 6에서 정규식 기반 검증
- [x] `.claude/skills/` 로컬 배치 결정 → Task 8
- [x] Placeholder 스캔: "TBD"·"implement later"·"similar to"·검증되지 않은 코드 스니펫 없음 확인
- 주의: SKILL.md·references/ 풀 콘텐츠는 Phase 1b로 이관(의도적). 현재 스킬은 결정론적 엔진만.
