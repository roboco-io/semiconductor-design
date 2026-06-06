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
    # 헤더 줄(Startpoint:/Endpoint:/Path Group: 등)은 컬럼 0에서 시작한다고 가정한다 — 선행 공백 불허.
    m = re.search(rf"^{label}:\s+(\S+)", block, re.MULTILINE)
    if m is None:
        raise ValueError(f"missing '{label}' in path block")
    return m.group(1)


def _is_ff(block: str, label: str) -> bool:
    # clock 주석은 긴 instance 이름에서 둘째 줄로 wrap된다 (실제 OpenSTA 포맷, F1).
    # label 줄부터 다음 헤더 직전까지의 clause를 떠서 "flip-flop"을 본다 — 단/두-줄 모두 처리.
    m = re.search(
        rf"^{label}:(.*?)(?=^Startpoint:|^Endpoint:|^Path Group:)",
        block,
        re.MULTILINE | re.DOTALL,
    )
    clause = m.group(1) if m else ""
    return "flip-flop" in clause


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
