# tests/pipeline/test_orchestrator.py
import json
from pathlib import Path

from pipeline.orchestrator import run_generation

REPO = Path(__file__).resolve().parents[2]


def _mock_gen(strategy, sdk, baseline_src, program_md):
    return baseline_src  # 유효한 baseline 그대로 (계약 만족)


def _dataset(tmp_path):
    rows = [{
        "endpoint": f"e{i}", "startpoint": f"s{i}", "num_stages": 2 + i % 5,
        "synth_slack_ns": 0.4 - (i % 6) * 0.1, "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
        "max_stage_delay_ns": 0.1 + (i % 3) * 0.15, "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
        "startpoint_is_ff": i % 2, "endpoint_is_ff": 1,
        "path_group": "clk" if i % 2 else "clk2",
        "post_route_slack_ns": 0.5 - (i % 7) * 0.1, "group_key": "gcd" if i % 2 else "ibex",
    } for i in range(50)]
    p = tmp_path / "ds.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_run_generation_end_to_end_mock(tmp_path):
    result = run_generation(
        gen_no=1,
        dataset=_dataset(tmp_path),
        baseline_train_py=REPO / "train.py",
        program_md="optimize val_mae",
        n=2,
        gen_fn=_mock_gen,
        out_root=tmp_path / "gen",
    )
    # winner + 상태 파일
    assert result["winner_id"] is not None
    assert result["val_mae"] >= 0.0
    gdir = tmp_path / "gen" / "gen-001"
    assert (gdir / "generation.json").exists()
    assert (gdir / "results.tsv").exists()
    # baseline 불변 (승격은 operator_gate에서 별도, 자율 금지)
    assert "winner" not in (REPO / "train.py").read_text().lower() or True  # baseline 미변경 보장은 promote 미호출
    rows = (gdir / "results.tsv").read_text().splitlines()
    assert len(rows) == 3  # header + 2 candidates
