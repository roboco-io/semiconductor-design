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


def test_join_keeps_only_matched_paths():
    rows = join_paths(_synth(), _route())
    keys = {(r["startpoint"], r["endpoint"]) for r in rows}
    assert keys == {("_0_", "_1_"), ("_3_", "_4_")}  # inp_a & _9_ dropped


def test_join_row_has_features_and_label():
    rows = join_paths(_synth(), _route())
    row = next(r for r in rows if r["startpoint"] == "_0_")
    assert row["num_stages"] == 4
    assert row["synth_slack_ns"] == 1.28
    assert row["post_route_slack_ns"] == 0.85


def test_group_key_prefixes_design_id():
    assert group_key("clk", "gcd") == "gcd:clk"
