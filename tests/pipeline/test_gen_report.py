# tests/pipeline/test_report.py
from pipeline.report import render_generation_report


def test_report_contains_all_sections():
    md = render_generation_report(
        gen_no=3,
        ranking=[("cand-001", "codex", "moderate", 0.099), ("cand-000", "claude", "conservative", 0.102)],
        winner_id="cand-001",
        t1_report="T1: verdict distinguishable",
        codex_verdict={"approve": True, "reasons": "계약 준수"},
        decision="promoted",
    )
    assert "gen-003" in md or "003" in md
    assert "cand-001" in md and "cand-000" in md       # 후보 순위
    assert "distinguishable" in md                       # T1
    assert "계약 준수" in md                              # Codex 사유
    assert "promoted" in md                              # 결정
