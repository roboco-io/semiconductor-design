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


def test_top_module_prefers_top_attribute():
    # flatten 후 미참조 모듈 정의가 남아도 yosys top 속성 모듈을 택한다 (microwatt 실측)
    nl = {
        "modules": {
            "leftover": {"ports": {}, "cells": {
                "_x_": {"type": "sky130_fd_sc_hd__inv_2", "connections": {"A": [2], "Y": [3]}}}},
            "real_top": {
                "attributes": {"top": "00000000000000000000000000000001"},
                "ports": {},
                "cells": {
                    "_ff_": {"type": "sky130_fd_sc_hd__dfxtp_1",
                             "connections": {"D": [4], "Q": [5]}}},
            },
        }
    }
    graphs = build_endpoint_graphs(nl)
    assert list(graphs) == ["_ff_"]


def test_top_module_ambiguous_without_attribute_raises():
    nl = {
        "modules": {
            "a": {"ports": {}, "cells": {
                "_x_": {"type": "sky130_fd_sc_hd__inv_2", "connections": {"A": [2], "Y": [3]}}}},
            "b": {"ports": {}, "cells": {
                "_y_": {"type": "sky130_fd_sc_hd__inv_2", "connections": {"A": [4], "Y": [5]}}}},
        }
    }
    import pytest

    with pytest.raises(ValueError, match="top"):
        build_endpoint_graphs(nl)


def test_multibit_output_port_endpoints_are_per_bit():
    # STA는 벡터 출력 포트를 비트 단위 endpoint(resp_msg[10])로 낸다 — 라벨 매칭 계약
    nl = {
        "modules": {
            "top": {
                "attributes": {"top": 1},
                "ports": {"o2": {"direction": "output", "bits": [5, 6]}},
                "cells": {
                    "_a_": {"type": "sky130_fd_sc_hd__inv_2", "connections": {"A": [2], "Y": [5]}},
                    "_b_": {"type": "sky130_fd_sc_hd__inv_2", "connections": {"A": [3], "Y": [6]}},
                },
            }
        }
    }
    graphs = build_endpoint_graphs(nl)
    assert "o2[0]" in graphs and "o2[1]" in graphs and "o2" not in graphs
    assert graphs["o2[0]"].nodes[0][0] == "_a_"
    assert graphs["o2[1]"].nodes[0][0] == "_b_"
