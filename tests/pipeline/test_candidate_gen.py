# tests/pipeline/test_candidate_gen.py
from pathlib import Path

from pipeline.candidate_gen import Candidate, generate_candidates


def _mock_gen(strategy, sdk, baseline_src, program_md):
    # 결정론적 가짜 변형: baseline 끝에 전략 주석을 붙인 유효한 train.py.
    return baseline_src + f"\n# variant: {sdk}/{strategy}\n"


def test_generates_n_candidates_split_across_sdks(tmp_path):
    cands = generate_candidates(
        baseline_src="print('base')\n",
        program_md="optimize val_mae",
        out_dir=tmp_path,
        n=4,
        gen_fn=_mock_gen,
    )
    assert len(cands) == 4
    sdks = {c.sdk for c in cands}
    assert sdks == {"claude", "codex"}  # split across both
    # 각 후보의 train.py가 디스크에 기록되고 변형이 반영됨
    for c in cands:
        src = (Path(c.src_path)).read_text()
        assert f"variant: {c.sdk}/{c.strategy}" in src
        assert c.patch_ref  # diff 기록


def test_candidate_ids_unique(tmp_path):
    cands = generate_candidates("x\n", "p", tmp_path, 3, _mock_gen)
    assert len({c.id for c in cands}) == 3
