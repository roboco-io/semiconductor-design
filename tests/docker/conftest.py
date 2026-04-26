"""Shared fixtures for tests/docker/*.

Tests in this directory require a local Docker daemon. A session-scoped
fixture skips the entire directory when ``docker version`` returns non-zero,
so CI jobs without Docker (pure unit-test runners) do not fail.

Tests marked ``requires_real_lockfile`` are skipped when the project's
``lockfile.yaml`` is in dry-run state (placeholder hex-word SHAs like
``deadbeef...`` / yosys-N.NN-DRY-RUN). This guards orfs-runner /
librelane-runner build tests from attempting ``git checkout`` with
non-existent SHAs. Once Phase E1 fills real upstream SHAs, these tests
start running automatically.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCKFILE_PATH = REPO_ROOT / "lockfile.yaml"

# Hex-word fake-SHA prefix patterns the dry-run lockfile uses (see Codex's
# Apr-26 lockfile fill; case-insensitive).
DRY_RUN_HEX_PREFIXES = ("deadbeef", "cafebabe", "feedface", "0badc0de", "00000000")
DRY_RUN_YOSYS_PATTERN = re.compile(r"-DRY-RUN", re.IGNORECASE)


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


def _is_dry_run_lockfile() -> bool:
    """Return True when lockfile.yaml carries placeholder SHAs.

    A SHA is considered placeholder when it starts with a known hex-word
    prefix. yosys is matched on the ``-DRY-RUN`` suffix in the tag string.
    Missing lockfile or missing keys → treat as dry-run (safer default).
    """
    if not LOCKFILE_PATH.exists():
        return True
    try:
        lockfile = yaml.safe_load(LOCKFILE_PATH.read_text())
    except (yaml.YAMLError, OSError):
        return True
    commit_shas = lockfile.get("commit_shas") or {}
    for key in ("openroad", "librelane", "open_pdks"):
        val = commit_shas.get(key)
        if not val or not isinstance(val, str):
            return True
        if val.lower().startswith(DRY_RUN_HEX_PREFIXES):
            return True
    yosys_tag = commit_shas.get("yosys")
    if not yosys_tag or not isinstance(yosys_tag, str):
        return True
    if DRY_RUN_YOSYS_PATTERN.search(yosys_tag):
        return True
    return False


@pytest.fixture(scope="session", autouse=True)
def _require_docker() -> None:
    if not _docker_available():
        pytest.skip("docker daemon unavailable", allow_module_level=True)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip ``requires_real_lockfile`` tests while lockfile is dry-run."""
    if not _is_dry_run_lockfile():
        return
    skip_dry_run = pytest.mark.skip(
        reason="lockfile.yaml is in dry-run state (placeholder hex-word SHAs); "
        "fill real upstream commit SHAs (Phase E1) to enable these tests"
    )
    for item in items:
        if "requires_real_lockfile" in item.keywords:
            item.add_marker(skip_dry_run)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
