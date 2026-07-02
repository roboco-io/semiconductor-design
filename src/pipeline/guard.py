"""encoder read-only 강제 — 게이트 이전 차단 (spec §7·§8).

정적 소스 검사(후보의 encoder 접근/재학습 시도) + SHA 재검증(변조 탐지) 2중.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

FORBIDDEN_PATTERNS = ("models/encoder", "encoder-v1", "pretrain/", "pretrain_lib")


def check_candidate_source(src: str) -> list[str]:
    return [p for p in FORBIDDEN_PATTERNS if p in src]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_frozen(encoder_path: str | Path, expected_sha: str) -> None:
    p = Path(encoder_path)
    if not p.exists():
        raise RuntimeError(f"frozen encoder 없음: {p}")
    actual = sha256_file(p)
    if actual != expected_sha:
        raise RuntimeError(
            f"frozen encoder SHA 불일치: expected {expected_sha[:12]}… actual {actual[:12]}…"
        )
