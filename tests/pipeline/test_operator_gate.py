# tests/pipeline/test_operator_gate.py
from pipeline.candidate_gen import Candidate
from pipeline.operator_gate import promote, summarize


def _c():
    return Candidate("cand-001", "moderate", "claude", "/x/train.py", "diff")


def test_summarize_lists_winner_and_ranking():
    text = summarize(_c(), 0.17, [(_c(), 0.17)], holdout_mae=0.19)
    assert "cand-001" in text and "0.17" in text and "0.19" in text


def test_promote_only_when_approved(tmp_path):
    # baseline + winner src
    baseline = tmp_path / "train.py"
    baseline.write_text("# baseline\n")
    winner_src = tmp_path / "cand" / "train.py"
    winner_src.parent.mkdir()
    winner_src.write_text("# winner variant\n")

    # 거절: baseline 불변
    changed = promote(winner_src, baseline, gen_no=1, approved=False, do_git=False)
    assert changed is False
    assert baseline.read_text() == "# baseline\n"

    # 승인: baseline이 winner로 승격
    changed = promote(winner_src, baseline, gen_no=1, approved=True, do_git=False)
    assert changed is True
    assert baseline.read_text() == "# winner variant\n"


def test_summarize_includes_validation_report():
    from pipeline.candidate_gen import Candidate
    from pipeline.operator_gate import summarize

    winner = Candidate("cand-1", "moderate", "codex", "/tmp/1/train.py", "diff")
    ranking = [(winner, 0.10)]
    report = "# 승격 검증 리포트 (advisory)\nverdict: distinguishable"
    out = summarize(winner, 0.10, ranking, validation_report=report)
    assert "승격 검증 리포트" in out
    assert "distinguishable" in out
