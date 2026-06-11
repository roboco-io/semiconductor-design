# tests/probe/test_run_probe_driver.py
"""드라이버 end-to-end — runtime 제한 위해 변형 1개(v1)만으로 LODO 2 fold."""

import math


def test_run_probe_end_to_end_v1_only(run_probe_mod, probe_dir, probe_rows):
    res = run_probe_mod.run_probe(probe_rows, {"v1_delta": probe_dir / "v1_delta.py"})
    assert res["designs"] == ["alpha", "beta"]
    assert len(res["naive"]) == 2
    assert set(res["results"]) == {"v1_delta"}
    assert all(math.isfinite(m) for m in res["results"]["v1_delta"])
    assert res["verdicts"]["v1_delta"] in {
        "transferable", "partial", "not_transferable", "unverifiable",
    }
    md = run_probe_mod.render_probe_report(res)
    assert "v1_delta" in md
