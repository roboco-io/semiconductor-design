"""PathRecord → feature/label row 변환 (순수 함수, frozen 계약)."""

from __future__ import annotations

from prepare_lib.report import PathRecord

FEATURE_NAMES = [
    "num_stages",
    "synth_slack_ns",
    "synth_arrival_ns",
    "max_stage_delay_ns",
    "mean_stage_delay_ns",
    "startpoint_is_ff",
    "endpoint_is_ff",
    "path_group",
]

LABEL_NAME = "post_route_slack_ns"


def extract_features(p: PathRecord) -> dict:
    delays = [s.delay_ns for s in p.stages]
    n = len(delays)
    return {
        "num_stages": n,
        "synth_slack_ns": p.slack_ns,
        "synth_arrival_ns": p.arrival_ns,
        "max_stage_delay_ns": max(delays) if delays else 0.0,
        "mean_stage_delay_ns": round(sum(delays) / n, 6) if n else 0.0,
        "startpoint_is_ff": int(p.startpoint_is_ff),
        "endpoint_is_ff": int(p.endpoint_is_ff),
        "path_group": p.path_group,
    }
