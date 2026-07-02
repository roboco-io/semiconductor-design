import json
from pathlib import Path

from pretrain_lib.graph import build_endpoint_graphs
from pretrain_lib.pretrain_loop import build_vocab, naive_baseline_loss, train_encoder

FIX = Path(__file__).parent / "fixtures" / "mini_netlist.json"


def _corpus():
    g = build_endpoint_graphs(json.loads(FIX.read_text()))
    # 미니 netlist 하나를 3개 설계처럼 복제 — 학습/검증 분리 로직 검증용
    return {"d1": g, "d2": g, "dval": g}


def test_vocab_deterministic():
    v1 = build_vocab(_corpus())
    v2 = build_vocab(_corpus())
    assert v1 == v2 and v1["<mask>"] == 0 and v1["<unk>"] == 1


def test_train_encoder_early_stop_and_report():
    corpus = _corpus()
    model, vocab, report = train_encoder(corpus, encoder_val_designs=["dval"],
                                         seed=0, max_epochs=5, patience=2)
    assert report["stopped_epoch"] <= 5
    assert len(report["val_curve"]) == report["stopped_epoch"]
    assert isinstance(report["naive_baseline_loss"], float)
    assert report["best_val_loss"] > 0


def test_vocab_built_from_train_designs_only():
    # spec §6.1 — encoder-val 전용 셀 타입은 vocab에 들어가면 안 된다 (<unk> 처리).
    from pretrain_lib.graph import EndpointGraph

    g_train = EndpointGraph("e", (("a", "and2_1", 1, 1, 0),), ())
    g_val = EndpointGraph("e", (("b", "xor2_1", 1, 1, 0),), ())
    _model, vocab, _report = train_encoder(
        {"t": {"e": g_train}, "v": {"e": g_val}},
        encoder_val_designs=["v"], seed=0, max_epochs=1, patience=1,
    )
    assert "and2_1" in vocab and "xor2_1" not in vocab


def test_naive_baseline_is_finite():
    corpus = _corpus()
    vocab = build_vocab(corpus)
    nb = naive_baseline_loss({"d1": corpus["d1"]}, {"dval": corpus["dval"]}, vocab)
    assert nb > 0


def test_train_encoder_minibatch_deterministic_same_seed():
    # mini-batch 전환(2026-07-03) 후에도 동일 seed → 동일 곡선 (재현성 invariant)
    corpus = _corpus()
    _, _, ra = train_encoder(corpus, ["dval"], seed=0, max_epochs=3, patience=5, batch_size=1)
    _, _, rb = train_encoder(corpus, ["dval"], seed=0, max_epochs=3, patience=5, batch_size=1)
    assert ra["val_curve"] == rb["val_curve"] and len(ra["val_curve"]) == 3
