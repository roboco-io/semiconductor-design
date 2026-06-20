# tests/pipeline/test_validation.py
import pytest
from pathlib import Path

from pipeline.validation import (
    candidate_fold_maes,
    design_fold_splits,
    fold_splits,
    naive_fold_maes,
    paired_comparison,
    render_crossdesign_report,
    render_validation_report,
    repeated_design_fold_splits,
    run_crossdesign_gate,
    run_crossdesign_validation_gate,
    run_validation_gate,
    verdict,
)

REPO = Path(__file__).resolve().parents[2]


def test_fold_splits_count_and_partition():
    splits = fold_splits(50, k=5, repeats=10, base_seed=0)
    assert len(splits) == 50  # 5 fold × 10 repeat
    tr, va = splits[0]
    assert sorted(tr + va) == list(range(50))  # train+val == 전체
    assert set(tr).isdisjoint(va)  # 겹침 없음
    assert 8 <= len(va) <= 12  # 50/5 ≈ 10


def test_fold_splits_deterministic():
    a = fold_splits(40, k=5, repeats=2, base_seed=7)
    b = fold_splits(40, k=5, repeats=2, base_seed=7)
    assert a == b  # 같은 seed → 같은 split (재현성)


def test_naive_fold_maes_handcomputed():
    rows = [
        {"synth_slack_ns": 0.5, "post_route_slack_ns": 0.2},  # |0.5-0.2|=0.3
        {"synth_slack_ns": 0.0, "post_route_slack_ns": -0.4},  # 0.4
        {"synth_slack_ns": 1.0, "post_route_slack_ns": 1.0},  # 0.0
    ]
    splits = [([0], [1, 2]), ([1], [0, 2])]
    maes = naive_fold_maes(rows, splits)
    assert maes[0] == (0.4 + 0.0) / 2  # val={1,2}
    assert maes[1] == (0.3 + 0.0) / 2  # val={0,2}


def _rows(n=40):
    return [
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
            "path_group": "core_clock",
            "post_route_slack_ns": 0.5 - (i % 7) * 0.1,
            "group_key": "gcd",
        }
        for i in range(n)
    ]


# --- Task 1: repeated_design_fold_splits + split 3-tuple 호환 (spec §3.1·§3.2) ---


def test_repeated_design_fold_splits_count_and_structure():
    groups = ["a", "b", "a", "c", "b", "c"]  # D=3 설계
    splits = repeated_design_fold_splits(groups, repeats=2, base_seed=0)
    assert len(splits) == 6  # D(3) × repeats(2)
    for tr, va, seed in splits:  # 3-tuple
        assert set(tr).isdisjoint(va)
        assert sorted(tr + va) == list(range(6))
        assert isinstance(seed, int)


def test_repeated_design_fold_splits_seed_assignment():
    groups = ["a", "b", "c"]
    splits = repeated_design_fold_splits(groups, repeats=3, base_seed=10)
    seeds = sorted({s for _, _, s in splits})
    assert seeds == [10, 11, 12]  # base_seed + r


def test_repeated_design_fold_splits_deterministic_sorted_order():
    # 비정렬 레이블이어도 fold 순서는 sorted(set(groups)) = [a,b,c]를 따른다(spec §3.1).
    groups = ["b", "a", "b", "c", "a"]
    splits = repeated_design_fold_splits(groups, repeats=1, base_seed=0)
    held_out = []
    for _tr, va, _s in splits:
        held_out.append(sorted({groups[i] for i in va}))
    assert held_out == [["a"], ["b"], ["c"]]  # held-out 설계 순서 = 정렬


def test_repeated_design_fold_splits_requires_two_designs():
    with pytest.raises(ValueError):
        repeated_design_fold_splits(["a", "a", "a"], repeats=2)


def test_naive_fold_maes_accepts_3tuple():
    rows = [
        {"synth_slack_ns": 0.5, "post_route_slack_ns": 0.2},  # 0.3
        {"synth_slack_ns": 0.0, "post_route_slack_ns": -0.4},  # 0.4
        {"synth_slack_ns": 1.0, "post_route_slack_ns": 1.0},  # 0.0
    ]
    # 3-tuple split (seed 무시)도 2-tuple과 같은 결과여야.
    s3 = [([0], [1, 2], 7), ([1], [0, 2], 99)]
    maes = naive_fold_maes(rows, s3)
    assert maes[0] == (0.4 + 0.0) / 2
    assert maes[1] == (0.3 + 0.0) / 2


def test_candidate_fold_maes_passes_3tuple_seed(monkeypatch):
    import pipeline.validation as V

    seen_seeds = []

    def fake_run_candidate(train_py, dataset, out_dir, seed=0):
        seen_seeds.append(seed)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / "model.joblib").write_text("x")
        return 1.0

    monkeypatch.setattr(V, "run_candidate", fake_run_candidate)
    monkeypatch.setattr(V, "score_holdout", lambda *a, **k: 1.0)
    rows = _rows(6)
    splits = [([0, 1], [2, 3], 5), ([2, 3], [0, 1], 8)]  # 3-tuple
    V.candidate_fold_maes(REPO / "train.py", rows, splits, Path("/tmp/x_unused"))
    assert seen_seeds == [5, 8]  # split의 seed가 run_candidate로 전달


def test_candidate_fold_maes_2tuple_defaults_seed0(monkeypatch):
    import pipeline.validation as V

    seen_seeds = []

    def fake_run_candidate(train_py, dataset, out_dir, seed=0):
        seen_seeds.append(seed)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / "model.joblib").write_text("x")
        return 1.0

    monkeypatch.setattr(V, "run_candidate", fake_run_candidate)
    monkeypatch.setattr(V, "score_holdout", lambda *a, **k: 1.0)
    rows = _rows(4)
    splits = [([0, 1], [2, 3]), ([2, 3], [0, 1])]  # 2-tuple (하위 호환)
    V.candidate_fold_maes(REPO / "train.py", rows, splits, Path("/tmp/y_unused"))
    assert seen_seeds == [0, 0]


# --- Task 2: run_crossdesign_validation_gate + 리포트 scheme 분기 (spec §3.3·§3.5) ---


def _toy_gate_rows():
    # 2설계 × 소수 행 — 빠른 실제 train.py 평가용.
    r = _rows(30)
    for i, row in enumerate(r):
        row["group_key"] = "gcd" if i % 2 == 0 else "aes"
    return r


def test_crossdesign_validation_gate_scheme_and_keys(tmp_path):
    rows = _toy_gate_rows()
    res = run_crossdesign_validation_gate(
        REPO / "train.py", REPO / "train.py", rows, tmp_path / "wd", repeats=2
    )
    assert res["scheme"] == "repeated_design_lodo"
    assert res["repeats"] == 2
    assert res["n_designs"] == 2
    # winner==baseline(같은 train.py) → 유의한 우열 없음 → distinguishable 아님.
    assert res["verdict_vs_baseline"] in ("indistinguishable", "worse")


def test_crossdesign_validation_gate_winner_fail_is_worse(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(2)\n")
    rows = _toy_gate_rows()
    res = run_crossdesign_validation_gate(broken, REPO / "train.py", rows, tmp_path / "wd2", repeats=2)
    assert res["verdict_vs_baseline"] == "worse"  # 부분실패 → 보수적 차단


def test_render_validation_report_crossdesign_scheme():
    res = {
        "scheme": "repeated_design_lodo",
        "repeats": 10,
        "n_designs": 3,
        "winner_folds": [1.0, 1.1],
        "baseline_folds": [1.2, 1.3],
        "naive_folds": [2.0, 2.1],
        "n_failed_winner": 0,
        "n_failed_baseline": 0,
        "n_folds": 2,
        "winner_vs_baseline": {
            "mean_diff": -0.2, "ci_low": -0.3, "ci_high": -0.1,
            "wilcoxon_p": 0.01, "effect_size": -1.5, "n_valid": 2,
        },
        "winner_vs_naive": {
            "mean_diff": -1.0, "ci_low": -1.1, "ci_high": -0.9,
            "wilcoxon_p": 0.01, "effect_size": -3.0, "n_valid": 2,
        },
        "verdict_vs_baseline": "distinguishable",
    }
    md = render_validation_report(res)
    assert "교차설계" in md  # 교차설계 제목/캡션
    assert "상관" in md  # 상관 caveat (단일설계 경고 대신)


def test_candidate_fold_maes_real_trainpy(tmp_path):
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)  # 5 fold (빠르게)
    maes = candidate_fold_maes(REPO / "train.py", rows, splits, tmp_path / "wd")
    assert len(maes) == 5
    assert all(m >= 0.0 and m != float("inf") for m in maes)


def test_candidate_fold_maes_broken_trainpy_inf(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    rows = _rows(40)
    splits = fold_splits(len(rows), k=5, repeats=1)
    maes = candidate_fold_maes(broken, rows, splits, tmp_path / "wd2")
    assert all(m == float("inf") for m in maes)  # 모든 fold 실패


def test_paired_comparison_a_better_than_b():
    # a(winner)가 b(baseline)보다 일관되게 낮음 → mean_diff<0, CI가 0 미만
    # diff가 상수가 아니어야 dz가 실제 음수(상수면 std≈0 → dz=0이 정상, 별도 테스트가 검증).
    a = [0.10, 0.11, 0.09, 0.12, 0.10]
    b = [0.15, 0.17, 0.13, 0.18, 0.15]
    c = paired_comparison(a, b, n_boot=2000, seed=0)
    assert c["mean_diff"] < 0
    assert c["ci_high"] < 0  # CI 전체가 0 미만 → 유의
    assert 0.0 <= c["wilcoxon_p"] <= 1.0
    assert c["effect_size"] < 0  # Cohen's dz 부호 = mean_diff 부호
    assert abs(c["effect_size"]) < 1000  # 부동소수점 잔차로 폭주하지 않음
    assert c["n_valid"] == 5


def test_paired_comparison_constant_diff_dz_zero():
    a = [0.10, 0.10, 0.10]
    b = [0.15, 0.15, 0.15]  # diffs all exactly -0.05 → std≈0
    c = paired_comparison(a, b, n_boot=500, seed=0)
    assert c["effect_size"] == 0.0  # std≈0 → dz=0 per spec


def test_paired_comparison_indistinguishable():
    a = [0.10, 0.11, 0.09, 0.12, 0.10]
    b = [0.10, 0.12, 0.08, 0.13, 0.09]  # 뒤섞임 → 차이가 0 근처
    c = paired_comparison(a, b, n_boot=2000, seed=0)
    assert c["ci_low"] < 0 < c["ci_high"]  # CI가 0을 포함


def test_verdict_branches():
    assert verdict({"wilcoxon_p": 0.01, "ci_low": -0.05, "ci_high": -0.01}) == "distinguishable"
    assert verdict({"wilcoxon_p": 0.4, "ci_low": -0.03, "ci_high": 0.02}) == "indistinguishable"
    assert verdict({"wilcoxon_p": 0.01, "ci_low": 0.01, "ci_high": 0.05}) == "worse"


def test_run_validation_gate_baseline_vs_itself(tmp_path):
    # winner == baseline (같은 train.py) → 구분 불가가 정상
    rows = _rows(40)
    res = run_validation_gate(
        REPO / "train.py",
        REPO / "train.py",
        rows,
        tmp_path / "gate",
        k=5,
        repeats=1,
        n_boot=1000,
    )
    assert res["verdict_vs_baseline"] == "indistinguishable"
    assert abs(res["winner_vs_baseline"]["mean_diff"]) < 0.05
    assert res["n_failed_winner"] == 0
    assert len(res["winner_folds"]) == 5


def test_run_validation_gate_unstable_winner(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    rows = _rows(40)
    res = run_validation_gate(
        broken,
        REPO / "train.py",
        rows,
        tmp_path / "gate2",
        k=5,
        repeats=1,
        n_boot=1000,
    )
    assert res["verdict_vs_baseline"] == "worse"  # 불안정 후보는 worse 처리
    assert res["n_failed_winner"] == 5


def test_render_report_contains_warning_and_models():
    res = {
        "winner_folds": [0.10, 0.11],
        "baseline_folds": [0.12, 0.13],
        "naive_folds": [1.40, 1.42],
        "n_failed_winner": 0,
        "n_failed_baseline": 0,
        "n_folds": 2,
        "single_design": True,
        "winner_vs_baseline": {
            "mean_diff": -0.02,
            "ci_low": -0.03,
            "ci_high": -0.01,
            "wilcoxon_p": 0.04,
            "effect_size": -1.2,
            "n_valid": 2,
        },
        "winner_vs_naive": {
            "mean_diff": -1.30,
            "ci_low": -1.35,
            "ci_high": -1.25,
            "wilcoxon_p": 0.04,
            "effect_size": -8.0,
            "n_valid": 2,
        },
        "verdict_vs_baseline": "distinguishable",
    }
    md = render_validation_report(res)
    assert "distinguishable" in md
    assert "단일 설계" in md  # 정직성 경고 블록
    assert "naive" in md and "baseline" in md and "winner" in md
    assert "T4" in md  # held-out 설계는 T4 필요 명시


def test_render_report_unstable_marks_validation_failure():
    res = {
        "winner_folds": [0.10, float("inf"), 0.11, float("inf"), 0.12],
        "baseline_folds": [0.12, 0.13, 0.14, 0.15, 0.16],
        "naive_folds": [1.40, 1.42, 1.41, 1.43, 1.44],
        "n_failed_winner": 5,
        "n_failed_baseline": 0,
        "n_folds": 5,
        "single_design": True,
        "winner_vs_baseline": None,
        "winner_vs_naive": None,
        "verdict_vs_baseline": "worse",
    }
    md = render_validation_report(res)
    assert "worse" in md
    assert "검증 불가" in md or "불안정" in md  # 통계적 열등이 아님을 명시


def test_paired_comparison_length_mismatch_raises():
    with pytest.raises(ValueError):
        paired_comparison([0.1, 0.2, 0.3], [0.1, 0.2], n_boot=100, seed=0)


def test_report_has_statistical_dependence_caveat():
    res = {
        "winner_folds": [0.10, 0.11],
        "baseline_folds": [0.12, 0.13],
        "naive_folds": [1.40, 1.42],
        "n_failed_winner": 0,
        "n_failed_baseline": 0,
        "n_folds": 2,
        "single_design": True,
        "winner_vs_baseline": {
            "mean_diff": -0.02,
            "ci_low": -0.03,
            "ci_high": -0.01,
            "wilcoxon_p": 0.04,
            "effect_size": -1.2,
            "n_valid": 2,
        },
        "winner_vs_naive": {
            "mean_diff": -1.30,
            "ci_low": -1.35,
            "ci_high": -1.25,
            "wilcoxon_p": 0.04,
            "effect_size": -8.0,
            "n_valid": 2,
        },
        "verdict_vs_baseline": "distinguishable",
    }
    md = render_validation_report(res)
    assert "상관" in md and ("낙관" in md or "과신" in md)  # 반복 fold 상관 → CI 낙관 caveat


# ---------------------------------------------------------------------------
# Task 1: design_fold_splits (LODO)
# ---------------------------------------------------------------------------


def test_design_fold_splits_lodo():
    groups = ["A", "A", "B", "C", "B"]  # 설계 3개
    splits = design_fold_splits(groups)
    assert len(splits) == 3  # 설계당 1 fold
    # 정렬-안정 순서: A, B, C
    tr0, va0 = splits[0]
    assert sorted(va0) == [0, 1]  # A 행
    assert sorted(tr0) == [2, 3, 4]  # 나머지
    for tr, va in splits:
        assert set(tr).isdisjoint(va)
        assert sorted(tr + va) == [0, 1, 2, 3, 4]


def test_design_fold_splits_single_design_raises():
    with pytest.raises(ValueError):
        design_fold_splits(["A", "A", "A"])


# ---------------------------------------------------------------------------
# Task 2: run_crossdesign_gate
# ---------------------------------------------------------------------------


def _multidesign_rows(n_per=14):
    rows = []
    for d in ("A", "B", "C"):
        for i in range(n_per):
            rows.append(
                {
                    "endpoint": f"{d}e{i}",
                    "startpoint": f"{d}s{i}",
                    "num_stages": 2 + i % 5,
                    "synth_slack_ns": 0.4 - (i % 6) * 0.1,
                    "synth_arrival_ns": 0.3 + (i % 4) * 0.2,
                    "max_stage_delay_ns": 0.1 + (i % 3) * 0.15,
                    "mean_stage_delay_ns": 0.05 + (i % 3) * 0.05,
                    "startpoint_is_ff": i % 2,
                    "endpoint_is_ff": 1,
                    "path_group": "core_clock",
                    "post_route_slack_ns": 0.5 - (i % 7) * 0.1,
                    "group_key": d,
                }
            )
    return rows


def test_crossdesign_gate_winner_equals_baseline(tmp_path):
    rows = _multidesign_rows()
    res = run_crossdesign_gate(REPO / "train.py", REPO / "train.py", rows, tmp_path / "cd")
    assert res["n_designs"] == 3
    assert res["single_design"] is False
    assert len(res["per_design"]) == 3
    assert abs(res["mean_gap"]) < 0.05  # 동일 모델 → 격차≈0
    assert res["verdict"] == "mixed"  # winner==baseline → 동수 → mixed


def test_crossdesign_gate_broken_winner_unverifiable(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("import sys; sys.exit(3)\n")
    res = run_crossdesign_gate(broken, REPO / "train.py", _multidesign_rows(), tmp_path / "cd2")
    assert res["verdict"] == "unverifiable"
    assert res["n_winner_better"] == 0


def test_crossdesign_gate_partial_failure(tmp_path, monkeypatch):
    import pipeline.validation as V

    rows = _multidesign_rows()  # 3 designs A,B,C
    # winner: fails (inf) on design A (fold 0), ok on B,C; baseline: ok on all
    seq = {"winner": [float("inf"), 0.10, 0.12], "baseline": [0.11, 0.11, 0.11]}

    def fake_cfm(train_py, rows_, splits, workdir):
        key = "winner" if "winner" in str(workdir) else "baseline"
        return list(seq[key])

    monkeypatch.setattr(V, "candidate_fold_maes", fake_cfm)
    res = run_crossdesign_gate("w.py", "b.py", rows, tmp_path / "pf")
    assert res["n_designs"] == 3
    assert res["n_valid"] == 2  # A excluded (inf)
    assert len(res["per_design"]) == 3  # 모든 설계가 표에 남음
    assert sum(1 for p in res["per_design"] if not p["valid"]) == 1
    assert res["verdict"] in ("generalizes_better", "worse", "mixed")
    assert res["mean_gap"] != float("inf")  # 유효 fold만 평균


# ---------------------------------------------------------------------------
# Task 3: render_crossdesign_report
# ---------------------------------------------------------------------------


def test_render_crossdesign_report():
    res = {
        "single_design": False,
        "n_designs": 3,
        "n_valid": 3,
        "n_winner_better": 2,
        "mean_gap": -0.03,
        "per_design": [
            {
                "design": "A",
                "winner_mae": 0.10,
                "baseline_mae": 0.13,
                "naive_mae": 1.4,
                "valid": True,
            },
            {
                "design": "B",
                "winner_mae": 0.12,
                "baseline_mae": 0.11,
                "naive_mae": 1.3,
                "valid": True,
            },
            {
                "design": "C",
                "winner_mae": 0.09,
                "baseline_mae": 0.15,
                "naive_mae": 1.5,
                "valid": True,
            },
        ],
        "verdict": "generalizes_better",
    }
    md = render_crossdesign_report(res)
    assert "generalizes_better" in md
    assert "A" in md and "B" in md and "C" in md  # 설계별 행
    assert "2/3" in md or "2 / 3" in md  # n_winner_better/n_designs
    assert "probe" in md  # 방향성 probe 명시
    assert "통계" in md and ("검정 불가" in md or "유의성" in md)  # 저표본 caveat
