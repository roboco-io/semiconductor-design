# tests/pipeline/test_orchestrator.py
import json
from pathlib import Path

from pipeline.orchestrator import run_generation

REPO = Path(__file__).resolve().parents[2]


def _mock_gen(strategy, sdk, baseline_src, program_md):
    return baseline_src  # 유효한 baseline 그대로 (계약 만족)


def _dataset(tmp_path):
    rows = [
        {
            "endpoint": f"e{i}",
            "startpoint": f"s{i}",
            "num_stages": 2 + i % 5,
            "synth_slack_ns": 0.4 - (i % 6) * 0.1,
            "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
            "max_stage_delay_ns": 0.1 + (i % 3) * 0.15,
            "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
            "startpoint_is_ff": i % 2,
            "endpoint_is_ff": 1,
            "path_group": "clk" if i % 2 else "clk2",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1,
            "group_key": "gcd" if i % 2 else "ibex",
        }
        for i in range(50)
    ]
    p = tmp_path / "ds.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_run_generation_end_to_end_mock(tmp_path):
    baseline = REPO / "train.py"
    baseline_content_before = baseline.read_bytes()
    baseline_mtime_before = baseline.stat().st_mtime

    result = run_generation(
        gen_no=1,
        dataset=_dataset(tmp_path),
        baseline_train_py=baseline,
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
    # H-B 불변: baseline 미변경 (promote 미호출 — 자율 머지 금지)
    assert baseline.read_bytes() == baseline_content_before, (
        "run_generation must NOT modify baseline train.py (H-B invariant)"
    )
    assert baseline.stat().st_mtime == baseline_mtime_before, (
        "baseline mtime changed — run_generation must not touch the file"
    )
    rows = (gdir / "results.tsv").read_text().splitlines()
    assert len(rows) == 3  # header + 2 candidates
    gen_meta = json.loads((gdir / "generation.json").read_text())
    assert gen_meta["metric"] == "median_val_mae"
    assert gen_meta["eval_seeds"] == [0, 1, 2, 3, 4]
    header = rows[0].split("\t")
    assert "median_val_mae" in header
    assert "per_seed_vals" in header


def test_per_seed_vals_inf_serialized_as_null(tmp_path):
    """단락된(inf) 후보의 per_seed_vals 셀이 RFC 8259 위반 Infinity가 아닌 null로 직렬화되는지."""

    def _gen(strategy, sdk, baseline_src, program_md):
        # codex 후보 하나만 깨진 train.py → per_seed가 inf로 단락
        if sdk == "codex":
            return "import sys; sys.exit(3)\n"
        return baseline_src

    run_generation(
        gen_no=1,
        dataset=_dataset(tmp_path),
        baseline_train_py=REPO / "train.py",
        program_md="optimize val_mae",
        n=2,
        gen_fn=_gen,
        out_root=tmp_path / "gen",
        seeds=(0, 1),
    )
    gdir = tmp_path / "gen" / "gen-001"
    rows = (gdir / "results.tsv").read_text().splitlines()
    header = rows[0].split("\t")
    id_idx = header.index("id")
    per_seed_idx = header.index("per_seed_vals")
    winner_idx = header.index("is_winner")
    sdk_idx = header.index("sdk")

    broken_cell = None
    winner_id = None
    for line in rows[1:]:
        cols = line.split("\t")
        # 단락된 후보 = codex sdk
        if cols[sdk_idx] == "codex":
            broken_cell = cols[per_seed_idx]
        if cols[winner_idx] == "True":
            winner_id = cols[id_idx]

    # inf가 json.loads로 에러 없이 파싱되고 null(None)을 포함
    assert broken_cell is not None
    parsed = json.loads(broken_cell)  # "Infinity"였다면 그대로 통과하나 None 검증으로 차단
    assert None in parsed
    assert "Infinity" not in broken_cell
    # 유효한(claude) 후보가 winner
    gen_meta = json.loads((gdir / "generation.json").read_text())
    valid_winner = gen_meta["winner_candidate_id"]
    assert winner_id == valid_winner
