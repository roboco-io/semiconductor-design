"""frozen encoder 로드 → endpoint 임베딩. prepare.py v2가 소비 (spec §5)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.model import GraphAutoencoder


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_encoder(path: str | Path):
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    vocab, config = ckpt["vocab"], ckpt["config"]
    model = GraphAutoencoder(
        len(vocab), config["hidden"], config["emb_dim"], config["n_layers"]
    )
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, vocab, config


def embed_endpoints(netlist: dict, model, vocab, config) -> dict[str, list[float]]:
    graphs = build_endpoint_graphs(netlist, config["max_depth"], config["max_nodes"])
    out: dict[str, list[float]] = {}
    with torch.no_grad():
        for ep in sorted(graphs):
            if not graphs[ep].nodes:
                continue
            out[ep] = [round(float(x), 6) for x in model.encode(graphs[ep], vocab)]
    return out
