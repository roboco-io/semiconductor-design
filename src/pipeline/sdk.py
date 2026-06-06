"""sdk — 실제 Claude Code / Codex headless 호출 gen_fn (비용 발생, Operator-gated).

테스트는 이 모듈을 import하지 않는다(주입 mock 사용). orchestrator CLI 실행 시에만 로드.
"""

from __future__ import annotations

import re
import subprocess

_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    # LLM이 ```python ... ``` 펜스로 감싸면 그 안의 코드만 추출.
    m = _FENCE.search(text)
    return m.group(1) if m else text


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
    return out + "\n" if out else baseline_src
