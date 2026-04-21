"""Unit tests for the metric-collector entrypoint.

metric_collector_main is imported both from the Docker container (ENTRYPOINT)
and from the local `semi-metric-collector` CLI. It must:

1. Read three .rpt files from $INPUT_S3_URI (file:// in tests, s3:// in prod).
2. Call semi_design_runner.metrics.parse_reports — NOT reimplement it
   (spec §5 / Codex #8 single-source-of-truth).
3. Write metrics.json (Metrics schema serialization) to $OUTPUT_S3_URI.
4. Return exit 0 on success, non-zero with a clear stderr message on failure.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from semi_design_runner import metric_collector_main
from semi_design_runner.schemas import Metrics


def _seed_fixtures(in_dir: Path) -> None:
    (in_dir / "synth").mkdir(parents=True)
    (in_dir / "signoff").mkdir(parents=True)
    (in_dir / "synth" / "synth.rpt").write_text(
        "=== gcd ===\n   Chip area for module:      12345.678 um^2\n",
    )
    (in_dir / "signoff" / "sta.rpt").write_text("slack:  0.480 ns (MET)\n")
    (in_dir / "signoff" / "drc.rpt").write_text("Total violations: 0\n")


def test_collector_writes_metrics_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    _seed_fixtures(in_dir)
    monkeypatch.setenv("RUN_ID", "01HMC")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{in_dir}")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "120.5")

    rc = metric_collector_main.main(argv=[])
    assert rc == 0
    out_file = out_dir / "runs" / "01HMC" / "staging" / "metrics" / "metrics.json"
    assert out_file.exists()
    parsed = json.loads(out_file.read_text())
    m = Metrics.model_validate(parsed)
    assert m.area_um2 == pytest.approx(12345.678)
    assert m.wns_ns == pytest.approx(0.480)
    assert m.drc_violations == 0
    assert m.runtime_s == pytest.approx(120.5)


def test_collector_reuses_parse_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex #8: parser implementation must live in metrics.py only."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    _seed_fixtures(in_dir)
    monkeypatch.setenv("RUN_ID", "01HMC2")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{in_dir}")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "1.0")

    called: list[tuple] = []
    import semi_design_runner.metrics as metrics_mod
    real = metrics_mod.parse_reports

    def spy(**kwargs):
        called.append(tuple(sorted(kwargs.keys())))
        return real(**kwargs)

    monkeypatch.setattr(metrics_mod, "parse_reports", spy)
    rc = metric_collector_main.main(argv=[])
    assert rc == 0
    assert called == [("drc_rpt", "runtime_s", "sta_rpt", "synth_rpt")]


def test_collector_missing_input_returns_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_dir = tmp_path / "out"
    monkeypatch.setenv("RUN_ID", "01HMC3")
    monkeypatch.setenv("STAGE", "metrics")
    monkeypatch.setenv("INPUT_S3_URI", f"file://{tmp_path}/does-not-exist")
    monkeypatch.setenv("OUTPUT_S3_URI", f"file://{out_dir}")
    monkeypatch.setenv("STAGE_RUNTIME_S", "1.0")

    rc = metric_collector_main.main(argv=[])
    # Exit-code contract: 3 == missing report file (per module docstring).
    # A regression routing missing input to 2 (env-missing) or 1 (unhandled
    # exception) would have silently passed `!= 0`; be specific.
    assert rc == 3
