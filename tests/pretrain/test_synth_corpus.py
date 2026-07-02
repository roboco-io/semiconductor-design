import json
from pathlib import Path
from types import SimpleNamespace

from synth_corpus import synth_one  # pretrain/ 디렉터리 — conftest에서 path 추가


def _fake_netlist(n_ff: int) -> dict:
    cells = {
        f"_ff{i}_": {"type": "sky130_fd_sc_hd__dfxtp_1",
                     "connections": {"D": [2 + i], "Q": [1000 + i]}}
        for i in range(n_ff)
    }
    return {"modules": {"top": {"ports": {}, "cells": cells}}}


def _fake_run(out_dir: Path, n_ff: int):
    def run(cmd, **kw):
        # docker 호출을 흉내: netlist.json을 심고 exit 0
        target = out_dir / "gcd" / "netlist.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(_fake_netlist(n_ff)))
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    return run


def test_synth_one_success(tmp_path):
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x",
                  tmp_path, run=_fake_run(tmp_path, n_ff=12))
    assert r["ok"] and (tmp_path / "gcd" / "netlist.json").exists()


def test_synth_one_nonzero_exit_is_exclusion(tmp_path):
    def run(cmd, **kw):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x", tmp_path, run=run)
    assert not r["ok"] and r["reason"] == "yosys synth exit code != 0"


def test_synth_one_too_few_endpoints_is_exclusion(tmp_path):
    # spec §5 제외 규칙 (b) — 합성 단계에서 판정
    r = synth_one({"name": "gcd", "platform": "sky130hd"}, "img@sha256:x",
                  tmp_path, run=_fake_run(tmp_path, n_ff=3))
    assert not r["ok"] and r["reason"] == "extracted endpoints < 10"
