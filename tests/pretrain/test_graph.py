# tests/pretrain/test_graph.py
import json
from pathlib import Path

from pretrain_lib.graph import build_endpoint_graphs, is_ff, normalize_cell

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _netlist():
    return json.loads(FIX.read_text())


def test_normalize_and_ff():
    assert normalize_cell("sky130_fd_sc_hd__dfxtp_1") == "dfxtp_1"
    assert normalize_cell("sky130_fd_sc_hs__and2_1") == "and2_1"
    assert is_ff("dfxtp_1") and not is_ff("and2_1")


def test_ff_endpoint_cone():
    graphs = build_endpoint_graphs(_netlist())
    g = graphs["_ff1_"]  # FF endpoint = 인스턴스명
    names = [n[0] for n in g.nodes]
    # D-입력 cone: _inv_ ← _and_ ← (_ff1_.Q 재진입) — endpoint 자신 포함
    assert "_ff1_" in names and "_inv_" in names and "_and_" in names
    depths = {n[0]: n[4] for n in g.nodes}
    assert depths["_ff1_"] == 0 and depths["_inv_"] == 1 and depths["_and_"] == 2


def test_output_port_endpoint_exists():
    graphs = build_endpoint_graphs(_netlist())
    assert "out_z" in graphs  # top output port endpoint
    assert any(n[0] == "_buf_" for n in graphs["out_z"].nodes)


def test_determinism():
    a = build_endpoint_graphs(_netlist())
    b = build_endpoint_graphs(_netlist())
    assert a == b


def test_max_nodes_cap():
    graphs = build_endpoint_graphs(_netlist(), max_nodes=2)
    assert len(graphs["_ff1_"].nodes) == 2
