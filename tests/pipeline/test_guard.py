# tests/pipeline/test_guard.py
import pytest

from pipeline.guard import check_candidate_source, verify_frozen


def test_clean_source_passes():
    src = "import numpy as np\nimport torch\nX = np.zeros((2, 2))\n"
    assert check_candidate_source(src) == []


def test_encoder_access_is_blocked():
    src = "import torch\nw = torch.load('models/encoder-v1.pt')\n"
    v = check_candidate_source(src)
    assert v and any("encoder" in x for x in v)


def test_pretrain_lib_import_is_blocked():
    assert check_candidate_source("from pretrain_lib.embed import load_encoder\n")


def test_verify_frozen_detects_mutation(tmp_path):
    p = tmp_path / "encoder-v1.pt"
    p.write_bytes(b"frozen-weights")
    import hashlib

    good = hashlib.sha256(b"frozen-weights").hexdigest()
    verify_frozen(p, good)  # OK — 예외 없음
    p.write_bytes(b"mutated!")
    with pytest.raises(RuntimeError, match="SHA"):
        verify_frozen(p, good)


def test_verify_frozen_missing_file(tmp_path):
    with pytest.raises(RuntimeError, match="없"):
        verify_frozen(tmp_path / "nope.pt", "0" * 64)


def test_orchestrator_blocks_violating_candidate(tmp_path):
    import csv

    from pipeline.orchestrator import run_generation

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"num_stages": 3, "synth_slack_ns": 0.5, "synth_arrival_ns": 1.0, '
        '"max_stage_delay_ns": 0.2, "mean_stage_delay_ns": 0.1, "startpoint_is_ff": 1, '
        '"endpoint_is_ff": 1, "path_group": "clk", "post_route_slack_ns": 0.3, '
        '"group_key": "d1"}\n' * 8
    )
    baseline = tmp_path / "train.py"
    baseline.write_text("import json\nprint(json.dumps({'val_mae': 1.0}))\n")

    def gen_fn(strategy, sdk, baseline_src, program_md):
        return "import torch\nw = torch.load('models/encoder-v1.pt')\n"  # 위반 소스

    run_generation(1, dataset, baseline, "prog", 1, gen_fn, tmp_path, auto=False)
    tsv = (tmp_path / "gen-001" / "results.tsv").read_text()
    rows = list(csv.reader(tsv.splitlines(), delimiter="\t"))
    assert rows[1][3] == "inf"  # median_val_mae — 실행 없이 무효
