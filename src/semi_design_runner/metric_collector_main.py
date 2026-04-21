"""Container ENTRYPOINT target for the semi/metric-collector image.

Wrapped by docker/entrypoints/run-stage.sh via STAGE_COMMAND. Reads the three
canonical report files (`synth/synth.rpt`, `signoff/sta.rpt`, `signoff/drc.rpt`)
from $INPUT_S3_URI, calls semi_design_runner.metrics.parse_reports — the
single source of truth for parsing, per spec §5 / Codex #8 — and writes
metrics.json (Metrics schema serialization) to the staging output path.

Exit codes:
- 0: success, metrics.json written.
- 2: one of RUN_ID / INPUT_S3_URI / OUTPUT_S3_URI env vars missing.
- 3: one of synth.rpt / sta.rpt / drc.rpt input files missing.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Sequence

from semi_design_runner import metrics as metrics_mod
from semi_design_runner.schemas import Metrics


def _resolve_path(uri: str) -> Path:
    if uri.startswith("file://"):
        return Path(uri[len("file://"):])
    if uri.startswith("s3://"):
        raise RuntimeError(
            "s3:// URIs must be resolved by run-stage.sh before calling "
            "metric_collector_main; use $STAGE_INPUT_DIR instead."
        )
    raise ValueError(f"Unsupported URI scheme: {uri!r}")


def main(argv: Sequence[str] | None = None) -> int:
    run_id = os.environ.get("RUN_ID")
    stage = os.environ.get("STAGE", "metrics")
    input_uri = os.environ.get("INPUT_S3_URI")
    output_uri = os.environ.get("OUTPUT_S3_URI")
    runtime_s = float(os.environ.get("STAGE_RUNTIME_S", "0"))
    if not all([run_id, input_uri, output_uri]):
        print(
            "metric_collector_main: RUN_ID/INPUT_S3_URI/OUTPUT_S3_URI required",
            file=sys.stderr,
        )
        return 2

    input_dir = Path(os.environ.get("STAGE_INPUT_DIR") or _resolve_path(input_uri))
    synth_rpt = input_dir / "synth" / "synth.rpt"
    sta_rpt = input_dir / "signoff" / "sta.rpt"
    drc_rpt = input_dir / "signoff" / "drc.rpt"

    for p in (synth_rpt, sta_rpt, drc_rpt):
        if not p.exists():
            print(f"metric_collector_main: missing report {p}", file=sys.stderr)
            return 3

    # Lookup through the module so tests can monkeypatch parse_reports (spec §5
    # / Codex #8 single-source-of-truth: parser lives in metrics.py only).
    metrics: Metrics = metrics_mod.parse_reports(
        synth_rpt=synth_rpt,
        sta_rpt=sta_rpt,
        drc_rpt=drc_rpt,
        runtime_s=runtime_s,
    )

    work_dir = os.environ.get("STAGE_WORK_DIR")
    if work_dir:
        out_dir = Path(work_dir)
    else:
        out_dir = _resolve_path(output_uri) / "runs" / run_id / "staging" / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics.model_dump(mode="json"), indent=2, sort_keys=True),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
