import json
from pathlib import Path

import torch

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder, recon_loss

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _graph():
    graphs = build_endpoint_graphs(json.loads(FIX.read_text()))
    return graphs["_ff1_"]


VOCAB = {"<mask>": 0, "<unk>": 1, "and2_1": 2, "inv_2": 3, "dfxtp_1": 4, "buf_1": 5}


def test_encode_shape_and_determinism():
    torch.manual_seed(0)
    m = GraphAutoencoder(vocab_size=len(VOCAB))
    m.eval()
    g = _graph()
    e1 = m.encode(g, VOCAB)
    e2 = m.encode(g, VOCAB)
    assert e1.shape == (32,)
    assert torch.allclose(e1, e2)


def test_masked_recon_loss_decreases():
    torch.manual_seed(0)
    m = GraphAutoencoder(vocab_size=len(VOCAB), hidden=32, emb_dim=16, n_layers=2)
    g = _graph()
    opt = torch.optim.Adam(m.parameters(), lr=0.01)
    mask_idx = [1]  # _inv_ 노드 type을 가리고 재구성
    first = last = None
    for _ in range(30):
        opt.zero_grad()
        logits, deg = m(g, VOCAB, mask_idx)
        loss = recon_loss(logits, deg, g, VOCAB, mask_idx)
        loss.backward()
        opt.step()
        lv = float(loss.detach())
        first = first if first is not None else lv
        last = lv
    assert last < first


def test_recon_loss_uses_logits_device():
    torch.manual_seed(0)
    m = GraphAutoencoder(vocab_size=len(VOCAB), hidden=32, emb_dim=16, n_layers=2)
    g = _graph()
    logits, deg = m(g, VOCAB, [1])
    loss = recon_loss(logits, deg, g, VOCAB, [1])
    assert loss.device == logits.device and torch.isfinite(loss)
