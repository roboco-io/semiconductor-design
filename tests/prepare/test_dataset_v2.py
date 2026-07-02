# tests/prepare/test_dataset_v2.py
import json
from pathlib import Path

import pytest
import torch

from prepare_lib.dataset import build_dataset_v2
from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder
from pretrain_lib.pretrain_loop import build_vocab

MINI_NL = Path(__file__).resolve().parents[1] / "pretrain" / "fixtures" / "mini_netlist.json"
CONFIG = {"hidden": 32, "emb_dim": 8, "n_layers": 2, "max_depth": 8, "max_nodes": 256}


@pytest.fixture()
def encoder_ckpt(tmp_path):
    nl = json.loads(MINI_NL.read_text())
    vocab = build_vocab({"d": build_endpoint_graphs(nl)})
    torch.manual_seed(0)
    m = GraphAutoencoder(len(vocab), CONFIG["hidden"], CONFIG["emb_dim"], CONFIG["n_layers"])
    p = tmp_path / "encoder-v1.pt"
    torch.save({"state_dict": m.state_dict(), "vocab": vocab, "config": CONFIG}, p)
    return p


def _reports_for_mini(tmp_path):
    """mini_netlist의 _ff1_ endpoint에 맞춘 synth/route report_checks 최소 fixture."""
    synth = tmp_path / "synth.rpt"
    route = tmp_path / "route.rpt"
    block = (
        "Startpoint: in_a (input port)\n"
        "Endpoint: _ff1_ (rising edge-triggered flip-flop clocked by clk)\n"
        "Path Group: clk\n"
        "Path Type: max\n\n"
        "   0.10    0.10 ^ _and_/X (sky130_fd_sc_hd__and2_1)\n"
        "   0.05    0.15 ^ _inv_/Y (sky130_fd_sc_hd__inv_2)\n"
        "   1.00   data arrival time\n"
        "   0.50   slack (MET)\n\n"
    )
    synth.write_text(block)
    route.write_text(block.replace("0.50   slack", "0.30   slack"))
    lock = tmp_path / "lock.txt"
    lock.write_text("orfs-lock")
    return synth, route, lock


def test_v2_rows_have_embeddings_and_manifest_anchors(tmp_path, encoder_ckpt):
    synth, route, lock = _reports_for_mini(tmp_path)
    cm = tmp_path / "corpus_manifest.yaml"
    cm.write_text("version: 1\n")
    rows, manifest = build_dataset_v2(
        synth, route, lock, "mini", MINI_NL, encoder_ckpt, cm
    )
    assert rows and all(f"emb_{i:02d}" in rows[0] for i in range(CONFIG["emb_dim"]))
    assert manifest["emb_dim"] == CONFIG["emb_dim"]
    assert len(manifest["encoder_sha"]) == 64
    assert len(manifest["corpus_manifest_sha"]) == 64
    assert manifest["emb_coverage"] == 1.0


def test_v2_low_coverage_fails_fast(tmp_path, encoder_ckpt):
    synth, route, lock = _reports_for_mini(tmp_path)
    # endpoint 이름을 netlist에 없는 것으로 바꿔 매칭 0% 유도
    synth.write_text(synth.read_text().replace("_ff1_", "_ghost_"))
    route.write_text(route.read_text().replace("_ff1_", "_ghost_"))
    cm = tmp_path / "corpus_manifest.yaml"
    cm.write_text("version: 1\n")
    with pytest.raises(ValueError, match="coverage"):
        build_dataset_v2(synth, route, lock, "mini", MINI_NL, encoder_ckpt, cm)
