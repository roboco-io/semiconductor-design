---
title: ADR Multi-Seed Median Selection
aliases: [adr-multiseed-median-selection, median harness]
type: decision
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[gate-chain]], [[generation-log]]
---

# ADR: 단일 seed → 5-seed median selection

- **일자**: 2026-06-07 (gen-002 위양성 계기)
- **상태**: Accepted

## 맥락
gen-002에서 codex 후보가 단일 seed=0 val_mae 0.0992로 winner 선택됐으나, 다중 seed 재평가에서
일반화 실패가 드러남. 53샘플·random split이라 seed별 val_mae가 0.05~0.16으로 출렁여 seed=0이 우연히
그 후보에 유리한 split이었을 뿐.

## 결정
selection 지표를 **5-seed median val_mae**로 교체. 단일 seed 선택은 노이즈 데이터에서 위양성을 만든다.

## 대안
- A안(채택): 5-seed median — seed 노이즈에 강건, winner의 일관성 측정.
- B안(기각): 단일 seed — 빠르지만 split 운에 좌우.

## 결과
- gen-002 재평가 시 단일-seed winner가 셋 중 꼴찌 → **gen-002 reject**. 위양성 차단.
- per_seed_vals `inf→null`(RFC 8259) 가드 추가. [[gate-chain]]의 첫 단으로 편입.
- co-evolution: 운영 마찰(위양성)이 평가 프로토콜 진화를 낳고, 진화한 프로토콜이 다시 결론을 뒤집음.

## 참고
- spec `docs/superpowers/specs/2026-06-06-multiseed-median-selection-design.md`.
