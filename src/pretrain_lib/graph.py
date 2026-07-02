"""netlist.json(Yosys write_json) → endpoint 중심 그래프. 결정성 보장 (spec §5)."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass

# sky130_fd_sc 표준셀 출력 포트 명명 규약 (blackbox라 port_directions 부재 — 규약 판정).
OUTPUT_PORTS = frozenset({"X", "Y", "Q", "Q_N", "Z", "COUT", "SUM", "GCLK"})
_CELL_PREFIX_RE = re.compile(r"^sky130_fd_sc_[a-z]+__")
_FF_PREFIXES = ("df", "sdf", "edf", "dl")

Node = tuple[str, str, int, int, int]  # (inst, cell_norm, fanin, fanout, depth)


@dataclass(frozen=True)
class EndpointGraph:
    endpoint: str
    nodes: tuple[Node, ...]
    edges: tuple[tuple[int, int], ...]  # (driver_idx, sink_idx)


def normalize_cell(cell_type: str) -> str:
    return _CELL_PREFIX_RE.sub("", cell_type)


def is_ff(cell_norm: str) -> bool:
    return cell_norm.startswith(_FF_PREFIXES)


def _top_module(netlist: dict) -> dict:
    mods = netlist["modules"]
    # 셀을 가진 모듈이 top (write_json 후 hierarchy -auto-top 전제로 1개).
    withcells = [m for m in mods.values() if m.get("cells")]
    if len(withcells) != 1:
        raise ValueError(f"top 모듈 판별 실패: cells 보유 모듈 {len(withcells)}개")
    return withcells[0]


def _index(mod: dict):
    """bit → driver inst, inst → (fanin bits, fanout count) 색인. 이름 정렬로 결정성."""
    driver_of: dict[int, str] = {}
    fanin_bits: dict[str, list[int]] = {}
    fanout: dict[str, int] = {}
    for inst in sorted(mod["cells"]):
        cell = mod["cells"][inst]
        ins, outs = [], []
        for port in sorted(cell["connections"]):
            bits = [b for b in cell["connections"][port] if isinstance(b, int)]
            (outs if port in OUTPUT_PORTS else ins).extend(bits)
        fanin_bits[inst] = ins
        for b in outs:
            driver_of[b] = inst
    sink_count: dict[int, int] = {}
    for inst in sorted(mod["cells"]):
        for b in fanin_bits[inst]:
            sink_count[b] = sink_count.get(b, 0) + 1
    for port in mod.get("ports", {}).values():
        if port["direction"] == "output":
            for b in port["bits"]:
                if isinstance(b, int):
                    sink_count[b] = sink_count.get(b, 0) + 1
    for inst in sorted(mod["cells"]):
        cell = mod["cells"][inst]
        outs = [b for p, bs in cell["connections"].items() if p in OUTPUT_PORTS
                for b in bs if isinstance(b, int)]
        fanout[inst] = sum(sink_count.get(b, 0) for b in outs)
    return driver_of, fanin_bits, fanout


def _cone(start_insts, driver_of, fanin_bits, fanout, cells, max_depth, max_nodes):
    nodes: list[Node] = []
    edges: list[tuple[str, str]] = []
    seen: dict[str, int] = {}
    q = deque((i, 0) for i in start_insts)
    while q and len(nodes) < max_nodes:
        inst, depth = q.popleft()
        if inst in seen:
            continue
        seen[inst] = len(nodes)
        cn = normalize_cell(cells[inst]["type"])
        nodes.append((inst, cn, len(fanin_bits[inst]), fanout[inst], depth))
        if depth >= max_depth:
            continue
        drivers = sorted({driver_of[b] for b in fanin_bits[inst] if b in driver_of})
        for d in drivers:
            edges.append((d, inst))
            q.append((d, depth + 1))
    idx = {n[0]: i for i, n in enumerate(nodes)}
    eidx = tuple(sorted((idx[a], idx[b]) for a, b in edges if a in idx and b in idx))
    return tuple(nodes), eidx


def build_endpoint_graphs(
    netlist: dict, max_depth: int = 8, max_nodes: int = 256
) -> dict[str, EndpointGraph]:
    mod = _top_module(netlist)
    driver_of, fanin_bits, fanout = _index(mod)
    cells = mod["cells"]
    graphs: dict[str, EndpointGraph] = {}
    for inst in sorted(cells):
        if is_ff(normalize_cell(cells[inst]["type"])):
            nodes, edges = _cone([inst], driver_of, fanin_bits, fanout, cells,
                                 max_depth, max_nodes)
            graphs[inst] = EndpointGraph(inst, nodes, edges)
    for pname in sorted(mod.get("ports", {})):
        port = mod["ports"][pname]
        if port["direction"] != "output":
            continue
        drivers = sorted({driver_of[b] for b in port["bits"]
                          if isinstance(b, int) and b in driver_of})
        if drivers:
            nodes, edges = _cone(drivers, driver_of, fanin_bits, fanout, cells,
                                 max_depth - 1, max_nodes)
            graphs[pname] = EndpointGraph(pname, nodes, edges)
    return graphs
