# gen-002 재판정 (5-seed median harness)

- **판정일**: 2026-06-07
- **사유**: gen-002는 단일 seed=0 selection으로 cand-001(codex)을 winner로 뽑았으나,
  다중 seed 검증에서 일반화되지 않음이 드러남. 새 median harness
  ([spec](../../docs/superpowers/specs/2026-06-06-multiseed-median-selection-design.md))로 공정 재평가.
- **프로토콜**: `run_candidate_multiseed`, seeds `[0,1,2,3,4]`, metric `median_val_mae`.

## 결과

| 모델 | median val_mae | per-seed [0,1,2,3,4] |
|---|---|---|
| **baseline (gen-001 winner, 현 train.py)** | **0.0865** ← 최저 | 0.1042, 0.1557, 0.0831, 0.0865, 0.0696 |
| gen-002 cand-000 (claude, conservative) | 0.0891 | 0.1022, 0.1602, 0.0891, 0.0786, 0.0567 |
| gen-002 cand-001 (codex, moderate) | 0.0992 ← 최악 | 0.0992, 0.1571, 0.0753, 0.1153, 0.0562 |

## 해석

- 단일 seed=0에서 winner였던 cand-001(codex, 0.0992)이 median에서는 **셋 중 꼴찌**.
  seed=0이 우연히 이 후보에 유리한 split이었을 뿐 — 단일 seed selection의 **위양성**.
- baseline(gen-001 winner)이 median 최저(0.0865)로, gen-002의 어떤 후보도 능가하지 못함.
- 평가 프로토콜 교체(single→median)만으로 ranking이 역전 → "에이전트가 baseline 능가"가
  측정 아티팩트일 수 있음을 실증. H-B(Operator 게이트 + 재검증)가 broken winner 승격을 차단.

## 판정: REJECT (Operator 승인 2026-06-07)

- gen-002 `generation.json` status `awaiting_operator` → `rejected`.
- `train.py`(gen-001 winner) **불변** — baseline 유지.
- co-evolution 학습은 INTENT.md Learnings에 기록.
