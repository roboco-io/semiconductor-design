"""Parse Yosys/OpenROAD/LibreLane report files into the Metrics schema.

This module is imported both from `semi_design_runner.cli` (local use)
and from the `semi/metric-collector` Docker container ENTRYPOINT, so the
parser logic has a single source of truth (spec §5 — no double maintenance).
"""
from __future__ import annotations

import re
from pathlib import Path

from semi_design_runner.schemas import Metrics


_AREA_RE = re.compile(r"Chip area for module:\s+([\d.]+)\s*um\^2")
_SLACK_RE = re.compile(r"slack:\s+(-?[\d.]+)\s*ns")
_DRC_RE = re.compile(r"Total violations:\s+(\d+)")


def parse_reports(
    *,
    synth_rpt: Path,
    sta_rpt: Path,
    drc_rpt: Path,
    runtime_s: float,
) -> Metrics:
    synth_text = synth_rpt.read_text()
    sta_text = sta_rpt.read_text()
    drc_text = drc_rpt.read_text()

    area_match = _AREA_RE.search(synth_text)
    if not area_match:
        raise ValueError(f"No chip area found in {synth_rpt}")
    area_um2 = float(area_match.group(1))

    slack_match = _SLACK_RE.search(sta_text)
    wns_ns = float(slack_match.group(1)) if slack_match else None

    drc_match = _DRC_RE.search(drc_text)
    drc_violations = int(drc_match.group(1)) if drc_match else 0

    return Metrics(
        area_um2=area_um2,
        power_mw=None,  # sky130 open flow does not emit power by default
        max_freq_mhz=None,  # L3 to add when clock sweep is enabled
        wns_ns=wns_ns,
        tns_ns=None,
        drc_violations=drc_violations,
        runtime_s=runtime_s,
    )
