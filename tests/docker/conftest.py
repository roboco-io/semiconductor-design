"""Shared fixtures for tests/docker/*.

Tests in this directory require a local Docker daemon. A session-scoped
fixture skips the entire directory when `docker version` returns non-zero,
so CI jobs without Docker (pure unit-test runners) do not fail.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


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


@pytest.fixture(scope="session", autouse=True)
def _require_docker() -> None:
    if not _docker_available():
        pytest.skip("docker daemon unavailable", allow_module_level=True)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT
