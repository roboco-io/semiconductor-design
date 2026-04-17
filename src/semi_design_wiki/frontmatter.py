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
