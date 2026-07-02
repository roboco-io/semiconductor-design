"""encoder 사전학습 루프 — patience 조기 종료 + naive baseline (spec §6.2)."""

from __future__ import annotations

import sys

import torch

from pretrain_lib.model import GraphAutoencoder, graph_tensors, recon_loss

MASK_FRAC = 0.15


def build_vocab(graphs_by_design: dict[str, dict]) -> dict[str, int]:
    cells = sorted({n[1] for graphs in graphs_by_design.values()
                    for g in graphs.values() for n in g.nodes})
    return {"<mask>": 0, "<unk>": 1, **{c: i + 2 for i, c in enumerate(cells)}}


def _mask_indices(n: int, rng: torch.Generator) -> list[int]:
    k = max(1, int(n * MASK_FRAC))
    return torch.randperm(n, generator=rng)[:k].tolist()


def _epoch_loss(model, graphs, vocab, rng=None) -> float:
    total, count = 0.0, 0
    for design in sorted(graphs):
        for ep in sorted(graphs[design]):
            g = graphs[design][ep]
            if not g.nodes:
                continue
            if rng is None:  # 검증: 결정적 마스크(첫 노드)
                mask = [0]
            else:
                mask = _mask_indices(len(g.nodes), rng)
            logits, deg = model(g, vocab, mask)
            loss = recon_loss(logits, deg, g, vocab, mask)
            if model.training:
                loss.backward()
            total += float(loss.detach())
            count += 1
    return total / max(count, 1)


def naive_baseline_loss(train_graphs, val_graphs, vocab) -> float:
    """encoder-train 노드 feature 평균(type 빈도분포·degree 평균)으로 일괄 예측한 val loss."""
    freq = torch.zeros(len(vocab))
    degs = []
    for graphs in train_graphs.values():
        for g in graphs.values():
            ti, num, _ = graph_tensors(g, vocab)
            for t in ti:
                freq[t] += 1
            degs.append(num[:, :2])
    probs = (freq / freq.sum()).clamp(min=1e-9)
    mean_deg = torch.cat(degs).mean(dim=0)
    total, count = 0.0, 0
    for graphs in val_graphs.values():
        for g in graphs.values():
            ti, num, _ = graph_tensors(g, vocab)
            ce = -torch.log(probs[ti]).mean()
            mse = ((num[:, :2] - mean_deg) ** 2).mean()
            total += float(ce + 0.1 * mse)
            count += 1
    return total / max(count, 1)


def train_encoder(graphs_by_design, encoder_val_designs, seed=0, max_epochs=200,
                  patience=10, device="cpu", hidden=64, emb_dim=32, n_layers=3):
    torch.manual_seed(seed)
    train_g = {d: g for d, g in graphs_by_design.items() if d not in encoder_val_designs}
    val_g = {d: g for d, g in graphs_by_design.items() if d in encoder_val_designs}
    # spec §6.1: encoder-val은 검증 전용 — vocab 등 사전학습 산출물에 미기여(val-only 셀은 <unk>).
    vocab = build_vocab(train_g)
    model = GraphAutoencoder(len(vocab), hidden=hidden, emb_dim=emb_dim, n_layers=n_layers)
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    rng = torch.Generator().manual_seed(seed)

    best, best_state, since_best = float("inf"), None, 0
    train_curve, val_curve = [], []
    for epoch in range(1, max_epochs + 1):
        model.train()
        opt.zero_grad()
        train_curve.append(_epoch_loss(model, train_g, vocab, rng))
        opt.step()
        model.eval()
        with torch.no_grad():
            vl = _epoch_loss(model, val_g, vocab)
        val_curve.append(vl)
        if vl < best:
            best, since_best = vl, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            since_best += 1
        print(  # 장시간 학습 가시성 (stderr — stdout JSON 계약 불침범)
            f"epoch {epoch}/{max_epochs} train={train_curve[-1]:.4f} val={vl:.4f} "
            f"best={best:.4f} since_best={since_best}",
            file=sys.stderr, flush=True,
        )
        if since_best >= patience:  # spec §6.2: patience=10 (호출자가 전달)
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    report = {
        "train_curve": train_curve,
        "val_curve": val_curve,
        "best_val_loss": best,
        "naive_baseline_loss": naive_baseline_loss(train_g, val_g, vocab),
        "stopped_epoch": len(val_curve),
        "seed": seed,
    }
    return model, vocab, report
