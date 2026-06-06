"""후보 생성 — baseline train.py를 agent(gen_fn)로 변형해 N개 reversible 변형 생성."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

STRATEGIES = ["conservative", "moderate", "aggressive"]
SDKS = ["claude", "codex"]

GenFn = Callable[[str, str, str, str], str]


@dataclass(frozen=True)
class Candidate:
    id: str
    strategy: str
    sdk: str
    src_path: str
    patch_ref: str  # unified diff vs baseline


def generate_candidates(
    baseline_src: str,
    program_md: str,
    out_dir: Path,
    n: int,
    gen_fn: GenFn,
) -> list[Candidate]:
    out = Path(out_dir)
    cands: list[Candidate] = []
    for i in range(n):
        sdk = SDKS[i % len(SDKS)]
        strategy = STRATEGIES[i % len(STRATEGIES)]
        mutated = gen_fn(strategy, sdk, baseline_src, program_md)
        cid = f"cand-{i:03d}"
        cdir = out / cid
        cdir.mkdir(parents=True, exist_ok=True)
        src_path = cdir / "train.py"
        src_path.write_text(mutated, encoding="utf-8")
        diff = "".join(
            difflib.unified_diff(
                baseline_src.splitlines(keepends=True),
                mutated.splitlines(keepends=True),
                fromfile="baseline/train.py",
                tofile=f"{cid}/train.py",
            )
        )
        cands.append(Candidate(cid, strategy, sdk, str(src_path), diff))
    return cands
