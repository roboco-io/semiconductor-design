import json
from pathlib import Path

import torch

from pretrain_lib.embed import embed_endpoints, load_encoder, sha256_file
from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder
from pretrain_lib.pretrain_loop import build_vocab

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"
CONFIG = {"hidden": 32, "emb_dim": 16, "n_layers": 2, "max_depth": 8, "max_nodes": 256}


def _save_ckpt(tmp_path):
    nl = json.loads(FIX.read_text())
    vocab = build_vocab({"d": build_endpoint_graphs(nl)})
    torch.manual_seed(0)
    m = GraphAutoencoder(len(vocab), CONFIG["hidden"], CONFIG["emb_dim"], CONFIG["n_layers"])
    p = tmp_path / "encoder-v1.pt"
    torch.save({"state_dict": m.state_dict(), "vocab": vocab, "config": CONFIG}, p)
    return p, nl


def test_roundtrip_and_determinism(tmp_path):
    p, nl = _save_ckpt(tmp_path)
    model, vocab, config = load_encoder(p)
    e1 = embed_endpoints(nl, model, vocab, config)
    e2 = embed_endpoints(nl, model, vocab, config)
    assert e1 == e2
    assert "_ff1_" in e1 and len(e1["_ff1_"]) == CONFIG["emb_dim"]


def test_sha256_file(tmp_path):
    p, _ = _save_ckpt(tmp_path)
    s = sha256_file(p)
    assert len(s) == 64 and s == sha256_file(p)
