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


def _worst_max_by_endpoint(paths: list[PathRecord]) -> dict[str, PathRecord]:
    # endpoint는 stage 간 안정적 (F3). max(setup) path만, endpoint당 worst(min slack)를 남긴다.
    best: dict[str, PathRecord] = {}
    for p in paths:
        if p.path_type != "max":
            continue
        cur = best.get(p.endpoint)
        if cur is None or p.slack_ns < cur.slack_ns:
            best[p.endpoint] = p
    return best


def join_paths(synth: list[PathRecord], route: list[PathRecord]) -> list[dict]:
    # endpoint 단위 join (F3): path 정체성은 stage 간 불안정하므로 안정점인 endpoint로 묶는다.
    synth_by_ep = _worst_max_by_endpoint(synth)
    route_by_ep = _worst_max_by_endpoint(route)
    rows: list[dict] = []
    for ep, sp in synth_by_ep.items():
        rp = route_by_ep.get(ep)
        if rp is None:
            continue  # route 시점에 없는 endpoint (retiming 등) drop
        rows.append(
            {
                "endpoint": ep,
                "startpoint": sp.startpoint,
                # path_group은 extract_features가 채운다 (** 언팩).
                **extract_features(sp),
                LABEL_NAME: extract_label(rp),
            }
        )
    return rows
