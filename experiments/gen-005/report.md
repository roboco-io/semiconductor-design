# gen-005 리포트 (자율 승격 게이트)

**최종 결정: rejected_lodo**  ·  winner: `cand-001`

> ⚠️ 다설계 dataset 평가 — val_mae를 gen-001~003과 직접 비교 금지(설계 교체).

## 1) 후보 순위 (median val_mae, 낮을수록 좋음)
| 후보 | sdk | 전략 | median_val_mae |
|---|---|---|---|
| cand-001 ⭐ | codex | moderate | 3.6964 |
| cand-000 | claude | conservative | 3.7909 |
| cand-003 | codex | conservative | 3.8156 |
| cand-002 | claude | aggressive | 4.2725 |

## 2) 교차설계 LODO 게이트 (held-out 설계 일반화)
# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)

**verdict: worse**  ·  winner 우세 설계: 0/3  ·  평균 격차(winner−baseline): +0.0433

| 설계(held-out) | naive | baseline | winner | 검증 |
|---|---|---|---|---|
| aes | 1.7198 | 2.6795 | 2.7560 | ✅ |
| gcd | 1.4117 | 2.5208 | 2.5669 | ✅ |
| ibex | 12.8071 | 2.9618 | 2.9692 | ✅ |

> ⚠️ **저표본**: 설계 3개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지
> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을
> 포함한 nested resampling(within-design 게이트와 동일 한계).

## 3) T1 통계 게이트 (winner vs 현 baseline)
LODO 게이트 미통과 — T1 생략.

## 4) Codex 승격 심사관 (무결성·안전·품질)
- approve: **False**
- 사유: LODO 미통과 — 심사 생략

## 5) 승격 규칙
median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).
사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).