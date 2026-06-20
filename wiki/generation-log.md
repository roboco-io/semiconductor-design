---
title: Generation Log gen-001~004
aliases: [generation-log, 세대 로그]
type: concept
status: active
confidence: high
updated: 2026-06-19
sources:
  - wiki/raw/2026-06-19_note_gen-001-004-knowhow.md
related: [[evolution-loop]], [[gate-chain]], [[cross-design-generalization]]
---

# Generation Log — gen-001 ~ gen-004

> 세대별 결과 시계열. 같은 사건의 결정 렌즈는 ADR 페이지 참조.

## 핵심 내용
| 세대 | 일자 | dataset | 결과 | 노하우 |
|---|---|---|---|---|
| gen-001 | 06-06 | gcd 53샘플 | **promoted** | H-A/H-B 첫 실증, Codex winner ~0.11(naive 13.5×). FunctionTransformer pickle 마찰 |
| gen-002 | 06-07 | gcd 53샘플 | **reject** | 단일 seed 위양성 → [[adr-multiseed-median-selection]] |
| gen-003 | 06-08 | gcd | **auto-gate** | T1 게이트 + Codex 심사 첫 자율, [[adr-operator-empowerment-repivot]] |
| gen-004 | 06-19 | 3설계 혼합 | **rejected_lodo** | LODO가 비개선 winner 자동 차단(우세 1/3, 평균 +0.015). 혼합훈련 회복 재현 |
| gen-005 | 06-20 | 3설계 혼합 | **rejected_lodo** | harness 수정 검증(후보 4/4 유효). winner 우세 0/3(평균 +0.043) → 2세대 연속 일반화 후퇴 |
| gen-006 | 06-20 | 3설계 혼합 | **rejected_t1** | program.md 힌트 강화 후 첫 LODO **통과**(우세 2/3, 평균 −0.083, generalizes_better)! 그러나 T1(혼합 K-fold)서 worse → 차단. LODO↔T1 목표 충돌 표면화 |

**후속 (06-21)**: LODO↔T1 충돌 해소 — T1을 교차설계 repeated-LODO 통계 게이트로 재정의([[gate-chain]]).
gen-006 winner 재평가 시 혼합-T1 `worse` → 교차설계-T1 `distinguishable`(mean_diff −0.53, p=0.003)로
판정 반전 → 두 게이트가 다른 축(robustness↔accuracy) 측정 입증. 새 체인이었다면 gen-006은 승격 후보.

## gen-004 상세 (첫 자율+LODO)
- median winner cand-003(codex/conservative, val_mae 3.74)가 held-out LODO서 baseline 후퇴 → `worse` → 차단.
- 세 fold 전부 유효(부분실패 아님) = 진짜 일반화 후퇴. baseline 불변, 승격 0건.
- ibex held-out서 baseline·winner 모두 naive 4.3× 격파([[cross-design-generalization]]).
- cand-001 자연 도태(sklearn 규약 미충족 fit 크래시), cand-002 harness 버그(claude 산문 반환 → SyntaxError).

## 관통 패턴
- negative result도 산출물: 승격 0건도 "median-best ≠ 일반화-best, 게이트가 간극을 잡는다"를 실증.
- 사전 고정 판정 · 생성자 ≠ 판정자 · co-evolution([[gate-chain]]).

## 참고
- `experiments/gen-001..004/report.md`, `generation.json`. `INTENT.md` Learnings.
