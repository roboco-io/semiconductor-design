"""sdk — 실제 Claude Code / Codex CLI 호출 (구독 사용량 소모, 추가 LLM 과금 없음).

테스트는 이 모듈을 import하지 않는다(주입 mock 사용). orchestrator CLI 실행 시에만 로드.
"""

from __future__ import annotations

import ast
import re
import subprocess

_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    # LLM이 ```python ... ``` 펜스로 감싸면 그 안의 코드만 추출.
    m = _FENCE.search(text)
    return m.group(1) if m else text


def _looks_like_source(text: str) -> bool:
    """변형 결과가 train.py 소스인지 최소 검증 — 산문/채팅 메시지 반환(계약 위반)을 차단.

    gen-004 cand-002: claude가 소스 대신 "✅ …완료" 산문을 반환했는데 _extract_code가
    펜스 부재 시 산문 전체를 train.py로 기록 → SyntaxError. 이 가드가 False면 호출자는
    후보를 버리지 않고 baseline으로 fallback한다(runner가 정상 채점, 진화는 다음 후보로).
    """
    t = text.strip()
    if not t:
        return False
    # 구문 유효성: 순수 산문(gen-004)도, 산문 머리말+코드 혼합(gen-006 cand-000)도 ast.parse가
    # SyntaxError로 잡는다. 토큰 검사만으론 "코드부에 토큰이 있으나 전체는 안 파싱되는" 혼합을 놓침.
    try:
        ast.parse(t)
    except (SyntaxError, ValueError):
        return False
    # frozen 계약상 모든 train.py는 import + 함수 def를 갖고 stdout에 val_mae를 출력한다.
    # 세 구조 토큰의 AND — parseable하지만 train.py가 아닌 코드(예: `x=1`)를 거른다.
    return "import " in t and "def " in t and "val_mae" in t


def codex_review_fn(prompt: str) -> str:
    """승격 심사 prompt를 Codex CLI로 보내 raw 응답을 반환 (비용). 실패 시 빈 문자열 → reviewer가 block."""
    try:
        proc = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", prompt],
            capture_output=True,
            text=True,
            timeout=900,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def claude_codex_gen_fn(strategy: str, sdk: str, baseline_src: str, program_md: str) -> str:
    prompt = (
        f"{program_md}\n\n전략: {strategy}. 아래 train.py를 변형하라. "
        '제약: 단일 파일, sklearn+numpy/joblib/click만, {"val_mae"} stdout 출력 계약·'
        "8 FEATURE_NAMES·--data/--out/--seed CLI 불변. "
        "마크다운/설명 없이 변형된 train.py 전체 소스만 출력.\n\n"
        "--- baseline train.py ---\n" + baseline_src
    )
    if sdk == "claude":
        cmd = ["claude", "-p", "--dangerously-skip-permissions", prompt]
    else:  # codex
        cmd = ["codex", "exec", "--skip-git-repo-check", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return baseline_src
    if proc.returncode != 0:
        # 실패 시 baseline 그대로 (runner가 val_mae 산출, 진화는 다음 후보로).
        return baseline_src
    out = _extract_code(proc.stdout).strip()
    # 산문/계약 위반 출력이면 후보를 버리지 말고 baseline으로 fallback.
    if not out or not _looks_like_source(out):
        return baseline_src
    return out + "\n"
