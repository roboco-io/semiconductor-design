# tests/probe/test_probe_verdict.py
"""판정 규칙(naive 기준 사전 고정, spec §5) + 리포트 렌더."""

INF = float("inf")


def test_transferable_when_below_naive_on_all_designs(run_probe_mod):
    assert run_probe_mod.probe_verdict([1.0, 1.0], [1.5, 1.4]) == "transferable"


def test_partial_when_below_naive_on_one_design(run_probe_mod):
    assert run_probe_mod.probe_verdict([1.0, 2.0], [1.5, 1.4]) == "partial"


def test_not_transferable_when_above_naive(run_probe_mod):
    assert run_probe_mod.probe_verdict([2.0, 2.0], [1.5, 1.4]) == "not_transferable"


def test_tie_counts_as_not_below(run_probe_mod):
    # 동률은 naive 이상으로 취급(사전 고정 규칙 — 결과 보고 기준 이동 금지).
    assert run_probe_mod.probe_verdict([1.5, 1.4], [1.5, 1.4]) == "not_transferable"


def test_unverifiable_on_any_inf(run_probe_mod):
    assert run_probe_mod.probe_verdict([INF, 1.0], [1.5, 1.4]) == "unverifiable"


def test_render_report_has_naive_verdicts_and_caveat(run_probe_mod):
    res = {
        "designs": ["aes", "gcd"],
        "naive": [1.7198, 1.4117],
        "results": {"winner": [2.74, 2.51], "v1_delta": [1.2, 1.1]},
        "verdicts": {"v1_delta": "transferable"},
    }
    md = run_probe_mod.render_probe_report(res)
    assert "naive" in md
    assert "v1_delta" in md and "transferable" in md
    assert "winner" in md  # 대조군은 verdict 없이 수치만
    assert "2 fold" in md or "2-fold" in md  # 저표본 caveat 명기
