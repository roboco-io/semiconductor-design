"""self-supervised graph autoencoder — 마스킹-재구성 (spec §6, PreRoutGNN 근거).

pure torch 3-layer mean-aggregation message passing (PyG 미채택 — plan 편차 노트).
"""

from __future__ import annotations

import torch
from torch import nn

from pretrain_lib.graph import EndpointGraph

MASK, UNK = 0, 1


def graph_tensors(g: EndpointGraph, vocab: dict[str, int]):
    type_ids = torch.tensor([vocab.get(n[1], UNK) for n in g.nodes], dtype=torch.long)
    numeric = torch.tensor(
        [[float(n[2]), float(n[3]), float(n[4])] for n in g.nodes], dtype=torch.float32
    )
    numeric = torch.log1p(numeric)  # fanin/fanout/depth 스케일 안정화
    adj = torch.tensor(g.edges, dtype=torch.long).reshape(-1, 2)
    return type_ids, numeric, adj


class GraphAutoencoder(nn.Module):
    def __init__(self, vocab_size: int, hidden: int = 64, emb_dim: int = 32, n_layers: int = 3):
        super().__init__()
        self.type_emb = nn.Embedding(vocab_size, hidden)
        self.num_proj = nn.Linear(3, hidden)
        self.layers = nn.ModuleList(
            [nn.Linear(2 * hidden, hidden) for _ in range(n_layers)]
        )
        self.out_proj = nn.Linear(2 * hidden, emb_dim)
        self.type_head = nn.Linear(hidden, vocab_size)
        self.deg_head = nn.Linear(hidden, 2)

    def _node_repr(self, g: EndpointGraph, vocab, mask_idx=()):
        dev = self.type_emb.weight.device  # MPS/CPU — 입력 텐서를 모델 디바이스로 정렬
        type_ids, numeric, adj = (t.to(dev) for t in graph_tensors(g, vocab))
        if len(mask_idx):
            type_ids = type_ids.clone()
            type_ids[list(mask_idx)] = MASK
        h = self.type_emb(type_ids) + self.num_proj(numeric)
        n = h.shape[0]
        for layer in self.layers:
            agg = torch.zeros_like(h)
            cnt = torch.zeros(n, 1, device=dev)
            if adj.numel():
                agg = agg.index_add(0, adj[:, 1], h[adj[:, 0]])  # driver → sink
                cnt = cnt.index_add(0, adj[:, 1], torch.ones(adj.shape[0], 1, device=dev))
            agg = agg / cnt.clamp(min=1.0)
            h = torch.relu(layer(torch.cat([h, agg], dim=1)))
        return h

    def forward(self, g: EndpointGraph, vocab, mask_idx: list[int]):
        h = self._node_repr(g, vocab, mask_idx)
        return self.type_head(h[mask_idx]), self.deg_head(h)

    def encode(self, g: EndpointGraph, vocab) -> torch.Tensor:
        h = self._node_repr(g, vocab)
        ep = h[0]  # BFS 시작 = endpoint 노드 (graph.py 계약)
        pooled = h.mean(dim=0)
        return self.out_proj(torch.cat([ep, pooled]))


def recon_loss(logits, deg_pred, g: EndpointGraph, vocab, mask_idx) -> torch.Tensor:
    type_ids, numeric, _ = graph_tensors(g, vocab)
    ce = nn.functional.cross_entropy(logits, type_ids[list(mask_idx)])
    mse = nn.functional.mse_loss(deg_pred, numeric[:, :2])
    return ce + 0.1 * mse
