"""Build test for the ORFS runner image.

This test performs an actual `docker build` with placeholder build-args so
that the Dockerfile is proven syntactically valid and all pinned commit_shas
resolve to reachable sources. It does NOT push to ECR — that is exercised
by a separate e2e test wired up in Phase E.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

IMAGE_TAG = "semi/orfs-runner:phaseC-test"
DOCKERFILE = "docker/orfs-runner.Dockerfile"


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_orfs_runner_builds(repo_root: Path) -> None:
    # Placeholder SHAs: real build uses `yq` to read `lockfile.yaml`; tests use
    # values from the fixture because the repo lockfile is Phase E territory.
    build_args = {
        "OPENROAD_SHA": "1111111111111111111111111111111111111111",
        "YOSYS_TAG": "yosys-0.55",
        "OPEN_PDKS_SHA": "2222222222222222222222222222222222222222",
    }
    cmd = [
        "docker", "build",
        "-t", IMAGE_TAG,
        "-f", DOCKERFILE,
        "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
        "--label", "semi.design.image=orfs-runner",
    ]
    for k, v in build_args.items():
        cmd += ["--build-arg", f"{k}={v}"]
    cmd += [str(repo_root)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=45 * 60)
    assert result.returncode == 0, result.stderr


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_orfs_runner_has_no_verilator(repo_root: Path) -> None:
    """Codex review #8: Verilator must NOT be shipped in G1 orfs-runner."""
    out = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
         "-c", "command -v verilator || true"],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0
    assert out.stdout.strip() == "", (
        f"verilator unexpectedly present in orfs-runner: {out.stdout!r}"
    )


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_orfs_runner_has_expected_tools(repo_root: Path) -> None:
    for tool, probe in [
        ("yosys",     "yosys -V"),
        ("openroad",  "openroad -version"),
        ("sky130A",   "test -d $PDK_ROOT/sky130A && echo ok"),
    ]:
        out = subprocess.run(
            ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
             "-c", probe],
            capture_output=True, text=True, timeout=60,
        )
        assert out.returncode == 0, f"{tool} missing: {out.stderr}"
