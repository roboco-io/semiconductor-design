# tests/pipeline/test_sdk_extract.py
"""_extract_code / _looks_like_source — 에이전트 산문 반환(계약 위반) 차단 가드.

gen-004 cand-002 회귀: claude가 train.py 소스 대신 채팅 메시지("✅ …완료")를 반환했는데
_extract_code가 코드펜스 부재 시 산문 전체를 train.py로 기록 → ✅(U+2705) SyntaxError.
가드는 비-소스 출력을 감지해 claude_codex_gen_fn이 baseline으로 fallback하게 만든다.
"""

from pipeline import sdk

# cand-002가 실제로 반환한 산문(이모지 머리말 + 마크다운). train.py로 쓰면 SyntaxError.
PROSE = (
    "✅ **aggressive 후보(cand-002) 생성·검증 완료** — 루프 계약대로 "
    "`experiments/gen-004/candidates/cand-002/train.py`에 기록했습니다(채팅 덤프 대신)."
)

REAL_SOURCE = (
    "import click\n"
    "from sklearn.ensemble import HistGradientBoostingRegressor\n\n"
    "FEATURE_NAMES = ['num_stages']\n\n"
    "def main():\n"
    "    print('{\"val_mae\": 1.0}')\n"
)

# gen-006 cand-000 회귀: 산문 머리말(em-dash 포함) + 코드(펜스 없음). 토큰 검사는 코드부의
# import/def/val_mae를 보고 통과하지만, 첫 줄 산문이 SyntaxError(U+2014 등) → train.py로 쓰면 깨짐.
PROSE_THEN_CODE = (
    "전략: conservative — baseline 구조(HGB+ExtraTrees Voting)를 유지하고 튜닝했습니다.\n"
    + REAL_SOURCE
)


def test_extract_code_unwraps_python_fence():
    text = "잡담\n```python\nimport x\ndef f(): pass\n```\n끝"
    assert sdk._extract_code(text).strip() == "import x\ndef f(): pass"


def test_extract_code_returns_text_when_no_fence():
    # 펜스가 없으면 원문 그대로 반환 — 가드는 _looks_like_source가 담당.
    assert sdk._extract_code(REAL_SOURCE) == REAL_SOURCE


def test_looks_like_source_accepts_real_train_py():
    assert sdk._looks_like_source(REAL_SOURCE) is True


def test_looks_like_source_rejects_prose():
    # 핵심 회귀: 산문 메시지는 소스가 아니다.
    assert sdk._looks_like_source(PROSE) is False


def test_looks_like_source_rejects_prose_prefixed_code():
    # gen-006 cand-000 회귀: 산문 머리말 + 코드(펜스 없음)는 구문이 깨져 소스가 아니다.
    # 토큰(import/def/val_mae)은 있으나 ast.parse가 실패 → False여야 한다.
    assert sdk._looks_like_source(PROSE_THEN_CODE) is False


def test_looks_like_source_rejects_unparseable_with_tokens():
    # 토큰은 있으나 구문 오류(닫히지 않은 괄호) → ast.parse 실패 → False.
    bad = "import x\ndef f(:\n    val_mae = 1\n"
    assert sdk._looks_like_source(bad) is False


def test_looks_like_source_rejects_empty():
    assert sdk._looks_like_source("") is False
    assert sdk._looks_like_source("   \n  ") is False


def _patch_subprocess(monkeypatch, stdout, returncode=0):
    class _Proc:
        def __init__(self):
            self.stdout = stdout
            self.returncode = returncode

    monkeypatch.setattr(sdk.subprocess, "run", lambda *a, **k: _Proc())


def test_gen_fn_falls_back_to_baseline_on_prose(monkeypatch):
    # 에이전트가 산문을 반환하면 후보를 버리지 말고 baseline으로 fallback(runner가 채점).
    _patch_subprocess(monkeypatch, PROSE)
    out = sdk.claude_codex_gen_fn("aggressive", "claude", REAL_SOURCE, "program")
    assert out == REAL_SOURCE


def test_gen_fn_returns_mutation_on_valid_source(monkeypatch):
    mutated = REAL_SOURCE.replace("HistGradientBoosting", "RandomForest")
    _patch_subprocess(monkeypatch, mutated)
    out = sdk.claude_codex_gen_fn("moderate", "codex", REAL_SOURCE, "program")
    assert "RandomForest" in out
