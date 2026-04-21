from pathlib import Path

from semi_design_runner.metrics import parse_reports
from semi_design_runner.schemas import Metrics

FIX = Path(__file__).parent / "fixtures"


def test_parse_reports_clean_case():
    m = parse_reports(
        synth_rpt=FIX / "synth.rpt",
        sta_rpt=FIX / "sta.rpt",
        drc_rpt=FIX / "drc.rpt",
        runtime_s=120.5,
    )
    assert isinstance(m, Metrics)
    assert m.area_um2 > 0
    assert m.wns_ns is not None
    assert m.drc_violations == 0
    assert m.runtime_s == 120.5


def test_parse_reports_handles_missing_power():
    m = parse_reports(
        synth_rpt=FIX / "synth.rpt",
        sta_rpt=FIX / "sta.rpt",
        drc_rpt=FIX / "drc.rpt",
        runtime_s=1.0,
    )
    assert m.power_mw is None  # synth.rpt fixture has no power line
