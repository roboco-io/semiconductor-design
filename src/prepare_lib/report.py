"""OpenSTA report_checks 텍스트 → PathRecord (frozen 파서, NFR-2)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_STAGE_RE = re.compile(
    r"^\s*([\d.]+)\s+([\d.]+)\s+[v^]\s+(\S+)\s+\((sky130\S+)\)\s*$"
)
_SLACK_RE = re.compile(r"^\s*(-?[\d.]+)\s+slack", re.MULTILINE)
_ARRIVAL_RE = re.compile(r"^\s*([\d.]+)\s+data arrival time", re.MULTILINE)


@dataclass(frozen=True)
class Stage:
    cell: str
    pin: str
    delay_ns: float
    arrival_ns: float


@dataclass(frozen=True)
class PathRecord:
    startpoint: str
    endpoint: str
    path_group: str
    path_type: str
    slack_ns: float
    arrival_ns: float
    stages: tuple[Stage, ...]
    startpoint_is_ff: bool
    endpoint_is_ff: bool


def _field(block: str, label: str) -> str:
    m = re.search(rf"^{label}:\s+(\S+)", block, re.MULTILINE)
    if m is None:
        raise ValueError(f"missing '{label}' in path block")
    return m.group(1)


def _is_ff(block: str, label: str) -> bool:
    m = re.search(rf"^{label}:.*$", block, re.MULTILINE)
    return m is not None and "flip-flop" in m.group(0)


def _stages(block: str) -> tuple[Stage, ...]:
    out = []
    for line in block.splitlines():
        m = _STAGE_RE.match(line)
        if m:
            out.append(Stage(cell=m.group(4), pin=m.group(3),
                             delay_ns=float(m.group(1)), arrival_ns=float(m.group(2))))
    return tuple(out)


def parse_report(text: str) -> list[PathRecord]:
    blocks = re.split(r"(?=^Startpoint:)", text, flags=re.MULTILINE)
    records: list[PathRecord] = []
    for block in blocks:
        if not block.lstrip().startswith("Startpoint:"):
            continue
        slack = _SLACK_RE.search(block)
        arrival = _ARRIVAL_RE.search(block)
        if slack is None or arrival is None:
            raise ValueError("path block missing slack or arrival line")
        records.append(
            PathRecord(
                startpoint=_field(block, "Startpoint"),
                endpoint=_field(block, "Endpoint"),
                path_group=_field(block, "Path Group"),
                path_type=_field(block, "Path Type"),
                slack_ns=float(slack.group(1)),
                arrival_ns=float(arrival.group(1)),
                stages=_stages(block),
                startpoint_is_ff=_is_ff(block, "Startpoint"),
                endpoint_is_ff=_is_ff(block, "Endpoint"),
            )
        )
    return records
