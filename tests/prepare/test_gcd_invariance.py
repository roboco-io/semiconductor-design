# tests/prepare/test_gcd_invariance.py
# 파서(prepare_lib) 변경이 gcd 파싱을 바꾸지 않음을 보장(D6: frozen 비교성).
import json
from pathlib import Path
from prepare_lib.dataset import build_dataset

REPO = Path(__file__).resolve().parents[2]
GCD = REPO / "experiments/real-gcd-fargate"


def test_gcd_dataset_is_invariant():
    rows, _manifest = build_dataset(
        str(GCD / "synth.rpt"),
        str(GCD / "route.rpt"),
        str(GCD / "versions.txt"),
        "gcd",
    )
    committed = [
        json.loads(line)
        for line in (GCD / "dataset/dataset.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert rows == committed, "파서 변경이 gcd dataset을 바꿈 — frozen 비교성 위반(D6)"
