# tests/probe/conftest.py
"""probe 테스트 공용 — experiments/multidesign/probe 모듈 로더 + 2설계 합성 fixture."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = ROOT / "experiments" / "multidesign" / "probe"


def load_probe_module(name: str):
    spec = importlib.util.spec_from_file_location(name, PROBE_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def run_probe_mod():
    return load_probe_module("run_probe")


@pytest.fixture(scope="session")
def probe_dir():
    return PROBE_DIR


@pytest.fixture
def probe_rows():
    # 2설계, label 오프셋 정반대(실데이터 gcd 음수/aes 양수 모사). post_route는 학습 가능한
    # 관계(synth − 0.02×stages)로 생성 — 변형이 finite MAE를 내는지 보는 스모크용.
    rows = []
    for d, offset in (("alpha", -1.0), ("beta", 1.5)):
        for i in range(24):
            stages = 2 + i % 5
            synth_slack = offset + 0.05 * (i % 8)
            rows.append(
                {
                    "endpoint": f"{d}/e{i}",
                    "startpoint": f"{d}/s{i}",
                    "num_stages": stages,
                    "synth_slack_ns": synth_slack,
                    "synth_arrival_ns": 0.5 + 0.03 * (i % 6),
                    "max_stage_delay_ns": 0.1 + 0.015 * (i % 3),
                    "mean_stage_delay_ns": 0.05 + 0.005 * (i % 3),
                    "startpoint_is_ff": i % 2,
                    "endpoint_is_ff": (i + 1) % 2,
                    "path_group": "core_clock" if i % 2 else "io",
                    "post_route_slack_ns": synth_slack - 0.02 * stages,
                    "group_key": d,
                }
            )
    return rows
