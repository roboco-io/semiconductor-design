from pathlib import Path

from prepare_lib.report import PathRecord, Stage, parse_report

FIX = Path(__file__).parent / "fixtures"


def _parse(name: str) -> list[PathRecord]:
    return parse_report((FIX / name).read_text())


def test_parses_three_paths():
    paths = _parse("synth.rpt")
    assert len(paths) == 3


def test_first_path_header_fields():
    p = _parse("synth.rpt")[0]
    assert p.startpoint == "_0_"
    assert p.endpoint == "_1_"
    assert p.path_group == "clk"
    assert p.path_type == "max"
    assert p.slack_ns == 1.28
    assert p.arrival_ns == 0.72
    assert p.startpoint_is_ff is True
    assert p.endpoint_is_ff is True


def test_stages_exclude_non_library_lines():
    # only sky130 library cells count as stages
    p0 = _parse("synth.rpt")[0]
    assert len(p0.stages) == 4
    assert isinstance(p0.stages[0], Stage)
    assert p0.stages[2].cell == "sky130_fd_sc_hd__nand2_1"
    assert p0.stages[2].pin == "_2_/Y"
    assert p0.stages[2].delay_ns == 0.21


def test_input_port_startpoint_not_ff():
    port_path = _parse("synth.rpt")[2]
    assert port_path.startpoint == "inp_a"
    assert port_path.startpoint_is_ff is False
    assert len(port_path.stages) == 2  # buf + dfxtp, the (in) line excluded
