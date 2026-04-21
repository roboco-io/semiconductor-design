"""End-to-end container test for semi/metric-collector."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

# Module-level slow marker so the `built_image` fixture itself is docker-gated;
# otherwise collecting any test in this module would trigger a full wheel+docker
# build on every pytest run.
pytestmark = [pytest.mark.slow]

IMAGE_TAG = "semi/metric-collector:phaseC-test"
DOCKERFILE = "docker/metric-collector.Dockerfile"


@pytest.fixture(scope="module")
def built_image(repo_root: Path) -> str:
    # Clear stale wheels so the narrowed COPY glob in the Dockerfile
    # (dist/semi_design_runner-*.whl) only picks up the freshly-built wheel.
    # The CI path (docker/build-metric-collector.sh) already does this; this
    # closes the gap for direct `docker build` invocations from the fixture.
    shutil.rmtree(repo_root / "dist", ignore_errors=True)
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", "dist"],
        cwd=repo_root, check=True, capture_output=True, text=True,
    )
    r = subprocess.run(
        ["docker", "build", "-t", IMAGE_TAG, "-f", DOCKERFILE,
         "--label", "org.opencontainers.image.source=https://github.com/dohyunjung/semiconductor-design",
         "--label", "semi.design.image=metric-collector",
         str(repo_root)],
        capture_output=True, text=True, timeout=10 * 60,
    )
    assert r.returncode == 0, r.stderr
    return IMAGE_TAG


def test_metric_collector_produces_metrics_json(
    built_image: str, tmp_path: Path, repo_root: Path
) -> None:
    in_dir = tmp_path / "in"
    (in_dir / "synth").mkdir(parents=True)
    (in_dir / "signoff").mkdir(parents=True)
    (in_dir / "synth" / "synth.rpt").write_text(
        "Chip area for module:      987.654 um^2\n"
    )
    (in_dir / "signoff" / "sta.rpt").write_text("slack:  0.123 ns (MET)\n")
    (in_dir / "signoff" / "drc.rpt").write_text("Total violations: 0\n")
    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HDOCKER",
         "-e", "STAGE=metrics",
         "-e", "INPUT_S3_URI=file:///work/in",
         "-e", "OUTPUT_S3_URI=file:///work/out",
         "-e", "STAGE_RUNTIME_S=42.0",
         "-e", "STAGE_COMMAND=python -m semi_design_runner.metric_collector_main",
         "-v", f"{tmp_path}:/work",
         built_image],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    out_file = (
        tmp_path / "out" / "runs" / "01HDOCKER" / "staging" / "metrics" / "metrics.json"
    )
    assert out_file.exists(), r.stdout + r.stderr
    data = json.loads(out_file.read_text())
    assert data["area_um2"] == pytest.approx(987.654)
    assert data["runtime_s"] == pytest.approx(42.0)


def test_metric_collector_simulate_spot_reclaim(
    built_image: str, tmp_path: Path
) -> None:
    r = subprocess.run(
        ["docker", "run", "--rm",
         "-e", "RUN_ID=01HMC",
         "-e", "STAGE=metrics",
         "-e", "INPUT_S3_URI=file:///work/in",
         "-e", "OUTPUT_S3_URI=file:///work/out",
         "-e", "SIMULATE_SPOT_RECLAIM=1",
         "-e", "SIMULATE_SPOT_RECLAIM_DELAY_S=0",
         "-e", "STAGE_COMMAND=python -m semi_design_runner.metric_collector_main",
         "-v", f"{tmp_path}:/work",
         built_image],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 143, r.stderr
