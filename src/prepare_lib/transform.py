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


def extract_label(p: PathRecord) -> float:
    return p.slack_ns


def group_key(path_group: str, design_id: str) -> str:
    return f"{design_id}:{path_group}"


def join_paths(synth: list[PathRecord], route: list[PathRecord]) -> list[dict]:
    # path_type을 키에 포함해 max(setup)/min(hold) corner 혼동을 차단한다.
    route_by_key = {
        (p.startpoint, p.endpoint, p.path_group, p.path_type): p for p in route
    }
    rows: list[dict] = []
    for sp in synth:
        key = (sp.startpoint, sp.endpoint, sp.path_group, sp.path_type)
        rp = route_by_key.get(key)
        if rp is None:
            continue  # unmatched synth path dropped (no post-route label)
        rows.append(
            {
                "startpoint": sp.startpoint,
                "endpoint": sp.endpoint,
                # path_group은 extract_features가 채운다 (** 언팩과 중복 제거).
                **extract_features(sp),
                LABEL_NAME: extract_label(rp),
            }
        )
    return rows
