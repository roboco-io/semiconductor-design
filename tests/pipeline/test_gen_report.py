# tests/pipeline/test_report.py
from pipeline.report import render_generation_report


def test_report_contains_all_sections():
    md = render_generation_report(
        gen_no=3,
        ranking=[
            ("cand-001", "codex", "moderate", 0.099),
            ("cand-000", "claude", "conservative", 0.102),
        ],
        winner_id="cand-001",
        t1_report="T1: verdict distinguishable",
        codex_verdict={"approve": True, "reasons": "계약 준수"},
        decision="promoted",
    )
    assert "gen-003" in md or "003" in md
    assert "cand-001" in md and "cand-000" in md  # 후보 순위
    assert "distinguishable" in md  # T1
    assert "계약 준수" in md  # Codex 사유
    assert "promoted" in md  # 결정


def test_report_includes_lodo_section_when_provided():
    md = render_generation_report(
        gen_no=4,
        ranking=[("cand-001", "codex", "moderate", 0.099)],
        winner_id="cand-001",
        t1_report="T1: distinguishable",
        codex_verdict={"approve": True, "reasons": "ok"},
        decision="promoted",
        lodo_report="LODO-SENTINEL-XYZ",
    )
    assert "LODO-SENTINEL-XYZ" in md  # LODO 섹션 본문
    assert "교차설계" in md  # LODO 섹션 제목
    # LODO 섹션은 T1 섹션보다 앞에 온다 (게이트 순서와 동일)
    assert md.index("LODO-SENTINEL-XYZ") < md.index("T1: distinguishable")


def test_report_omits_lodo_section_when_none():
    md = render_generation_report(
        gen_no=4,
        ranking=[("cand-001", "codex", "moderate", 0.099)],
        winner_id="cand-001",
        t1_report="T1: distinguishable",
        codex_verdict={"approve": True, "reasons": "ok"},
        decision="promoted",
    )
    assert "교차설계" not in md


def test_report_includes_comparability_note():
    md = render_generation_report(
        gen_no=4,
        ranking=[("cand-001", "codex", "moderate", 0.099)],
        winner_id="cand-001",
        t1_report="T1: distinguishable",
        codex_verdict={"approve": True, "reasons": "ok"},
        decision="promoted",
        comparability_note="비교-금지-SENTINEL",
    )
    assert "비교-금지-SENTINEL" in md  # 세대 리포트에 비교성 경고 명기(spec §6)
