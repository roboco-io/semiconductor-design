# tests/probe/test_variants.py
"""변형 3개 계약 스모크 — candidate_fold_maes 왕복(학습→model.joblib→score_holdout)."""

import math

from pipeline.validation import candidate_fold_maes, design_fold_splits


def _smoke(script, probe_rows, tmp_path):
    splits = design_fold_splits([r["group_key"] for r in probe_rows])
    maes = candidate_fold_maes(script, probe_rows, splits[:1], tmp_path)
    assert len(maes) == 1
    assert math.isfinite(maes[0])  # inf면 계약 위반(학습 실패/모델 미저장/채점 실패)


def test_v1_delta_contract_roundtrip(probe_dir, probe_rows, tmp_path):
    _smoke(probe_dir / "v1_delta.py", probe_rows, tmp_path)


def test_v2_groupstat_contract_roundtrip(probe_dir, probe_rows, tmp_path):
    _smoke(probe_dir / "v2_groupstat.py", probe_rows, tmp_path)
