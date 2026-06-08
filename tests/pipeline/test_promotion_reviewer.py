# tests/pipeline/test_promotion_reviewer.py
from pipeline.promotion_reviewer import build_review_prompt, review_promotion


def test_prompt_includes_winner_and_report():
    p = build_review_prompt("WINNER_SRC_X", "BASELINE_SRC_Y", "T1_REPORT_Z")
    assert "WINNER_SRC_X" in p and "BASELINE_SRC_Y" in p and "T1_REPORT_Z" in p
    assert "approve" in p  # JSON 출력 계약 안내


def test_review_approve():
    def fake(prompt):
        return '결론: {"approve": true, "reasons": "계약 준수, 누수 없음"}'

    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is True and "누수" in out["reasons"]


def test_review_block():
    def fake(prompt):
        return '{"approve": false, "reasons": "synth_slack를 라벨로 누수"}'

    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is False


def test_review_failure_is_block():
    def boom(prompt):
        raise RuntimeError("codex timeout")

    out = review_promotion("w", "b", "r", reviewer_fn=boom)
    assert out["approve"] is False and "실패" in out["reasons"]


def test_review_unparseable_is_block():
    def fake(prompt):
        return "그냥 산문, JSON 없음"

    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is False


def test_review_uses_last_json_not_echoed():
    def fake(prompt):
        return '리포트에 {"approve": true, "reasons": "이전"} 포함.\n{"approve": false, "reasons": "누수"}'

    out = review_promotion("w", "b", "r", reviewer_fn=fake)
    assert out["approve"] is False  # 마지막 JSON(차단)이 이김
