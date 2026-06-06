from pathlib import Path

from prepare_lib.report import parse_report
from prepare_lib.transform import FEATURE_NAMES, extract_features, extract_label, group_key, join_paths

FIX = Path(__file__).parent / "fixtures"


def _synth():
    return parse_report((FIX / "synth.rpt").read_text())


def _route():
    return parse_report((FIX / "route.rpt").read_text())


def test_feature_names_frozen_order():
    assert FEATURE_NAMES == [
        "num_stages", "synth_slack_ns", "synth_arrival_ns",
        "max_stage_delay_ns", "mean_stage_delay_ns",
        "startpoint_is_ff", "endpoint_is_ff", "path_group",
    ]


def test_extract_features_first_path():
    f = extract_features(_synth()[0])
    assert f["num_stages"] == 4
    assert f["synth_slack_ns"] == 1.28
    assert f["synth_arrival_ns"] == 0.72
    assert f["max_stage_delay_ns"] == 0.36
    assert f["mean_stage_delay_ns"] == 0.18
    assert f["startpoint_is_ff"] == 1
    assert f["endpoint_is_ff"] == 1
    assert f["path_group"] == "clk"


def test_features_cover_exactly_feature_names():
    f = extract_features(_synth()[0])
    assert set(f.keys()) == set(FEATURE_NAMES)


def test_extract_label_is_route_slack():
    assert extract_label(_route()[0]) == 0.85


def test_join_matches_on_endpoint_not_path():
    # 기존 fixture: 공통 endpoint = _1_, _4_ (inp_a→_5_, _9_→_10_ 는 한쪽만)
    rows = join_paths(_synth(), _route())
    assert {r["endpoint"] for r in rows} == {"_1_", "_4_"}


def test_join_row_has_features_and_label():
    rows = join_paths(_synth(), _route())
    row = next(r for r in rows if r["endpoint"] == "_1_")
    assert row["startpoint"] == "_0_"  # synth-stage worst path's startpoint
    assert row["num_stages"] == 4
    assert row["synth_slack_ns"] == 1.28
    assert row["post_route_slack_ns"] == 0.85
    assert row["path_group"] == "clk"


def test_join_drops_path_type_mismatch():
    # 같은 (startpoint, endpoint, path_group)라도 path_type(max/min)이 다르면 매칭되지 않고 drop.
    synth_max = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.50   data arrival time\n           0.10   slack (MET)"
    )
    route_min = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: min\n"
        "   0.50   data arrival time\n           0.20   slack (MET)"
    )
    rows = join_paths(parse_report(synth_max), parse_report(route_min))
    assert rows == []


def test_join_matches_on_endpoint_despite_disjoint_paths():
    # F3 핵심: synth worst path(via a)와 route worst path(via x)의 내부 게이트가 달라도
    # endpoint b가 공통이면 join된다. (sp,ep) 키였으면 0 rows였을 시나리오.
    synth = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.40    0.40 ^ a/Q (sky130_fd_sc_hd__dfxtp_1)\n"
        "   0.30    0.70 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.70   data arrival time\n           0.30   slack (MET)"
    )
    route = (
        "Startpoint: x (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.55    0.55 ^ x/Q (sky130_fd_sc_hd__dfxtp_1)\n"
        "   0.40    0.95 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.95   data arrival time\n           0.05   slack (MET)"
    )
    rows = join_paths(parse_report(synth), parse_report(route))
    assert len(rows) == 1
    assert rows[0]["endpoint"] == "b"
    assert rows[0]["startpoint"] == "a"
    assert rows[0]["post_route_slack_ns"] == 0.05


def test_join_keeps_worst_slack_per_endpoint():
    # endpoint b로 가는 synth max path 2개 중 worst(min slack=0.10)가 feature가 된다.
    synth = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.30    0.30 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.30   data arrival time\n           0.50   slack (MET)\n\n"
        "Startpoint: c (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.60    0.60 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.60   data arrival time\n           0.10   slack (MET)"
    )
    route = (
        "Startpoint: a (rising edge-triggered flip-flop clocked by clk)\n"
        "Endpoint: b (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\nPath Type: max\n"
        "   0.30    0.30 ^ b/D (sky130_fd_sc_hd__dfxtp_1)\n"
        "           0.30   data arrival time\n           0.20   slack (MET)"
    )
    rows = join_paths(parse_report(synth), parse_report(route))
    assert len(rows) == 1
    assert rows[0]["synth_slack_ns"] == 0.10


def test_group_key_prefixes_design_id():
    assert group_key("clk", "gcd") == "gcd:clk"
