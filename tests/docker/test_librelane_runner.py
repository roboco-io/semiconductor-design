"""Build and ENTRYPOINT contract tests for semi/librelane-runner.

The LibreLane project ships a first-party Nix flake (spec §5, K1 γ #2).
We consume it via the `librelane/librelane:<pinned-ref>` prebuilt image
as the FROM base, then inject our shared run-stage.sh ENTRYPOINT so the
SFN Map state can treat it interchangeably with semi/orfs-runner.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

IMAGE_TAG = "semi/librelane-runner:phaseC-test"
DOCKERFILE = "docker/librelane-runner.Dockerfile"


def _build_args_from_lockfile(repo_root: Path) -> dict[str, str]:
    lockfile = yaml.safe_load((repo_root / "lockfile.yaml").read_text())
    digest = lockfile["container_digests"]["librelane_base"]
    return {
        "LIBRELANE_DIGEST": digest.removeprefix("sha256:"),
        "LIBRELANE_REF": lockfile["commit_shas"]["librelane"],
        "OPEN_PDKS_SHA": lockfile["commit_shas"]["open_pdks"],
    }


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_librelane_runner_builds(repo_root: Path) -> None:
    build_args = _build_args_from_lockfile(repo_root)
    cmd = [
        "docker", "build",
        "-t", IMAGE_TAG,
        "-f", DOCKERFILE,
        "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
        "--label", "semi.design.image=librelane-runner",
    ]
    for k, v in build_args.items():
        cmd += ["--build-arg", f"{k}={v}"]
    cmd += [str(repo_root)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60 * 60)
    assert result.returncode == 0, result.stderr


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_librelane_runner_honors_simulate_spot_reclaim(tmp_path: Path) -> None:
    """Same KG-D contract as orfs-runner: SIMULATE_SPOT_RECLAIM=1 → exit 143."""
    (tmp_path / "in").mkdir()
    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HLL",
         "-e", "STAGE=pnr",
         "-e", "INPUT_S3_URI=file:///work/in",
         "-e", "OUTPUT_S3_URI=file:///work/out",
         "-e", "SIMULATE_SPOT_RECLAIM=1",
         "-e", "SIMULATE_SPOT_RECLAIM_DELAY_S=0",
         "-e", "STAGE_COMMAND=echo should-not-run",
         "-v", f"{tmp_path}:/work",
         IMAGE_TAG],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 143, r.stderr


@pytest.mark.slow
@pytest.mark.requires_real_lockfile
def test_librelane_runner_has_librelane(repo_root: Path) -> None:
    out = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "sh", IMAGE_TAG,
         "-c", "librelane --version"],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert (out.stdout + out.stderr).strip()
