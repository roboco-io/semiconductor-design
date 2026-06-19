# gen-006 리포트 (자율 승격 게이트)

**최종 결정: rejected_t1**  ·  winner: `cand-001`

> ⚠️ 다설계 dataset 평가 — val_mae를 gen-001~003과 직접 비교 금지(설계 교체).

## 1) 후보 순위 (median val_mae, 낮을수록 좋음)
| 후보 | sdk | 전략 | median_val_mae |
|---|---|---|---|
| cand-001 ⭐ | codex | moderate | 3.5021 |
| cand-002 | claude | aggressive | 3.9235 |
| cand-003 | codex | conservative | 4.4767 |
| cand-000 | claude | conservative | inf |

## 2) 교차설계 LODO 게이트 (held-out 설계 일반화)
# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)

**verdict: generalizes_better**  ·  winner 우세 설계: 2/3  ·  평균 격차(winner−baseline): -0.0834

| 설계(held-out) | naive | baseline | winner | 검증 |
|---|---|---|---|---|
| aes | 1.7198 | 2.6795 | 2.2023 | ✅ |
| gcd | 1.4117 | 2.5208 | 2.3574 | ✅ |
| ibex | 12.8071 | 2.9618 | 3.3524 | ✅ |

> ⚠️ **저표본**: 설계 3개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지
> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을
> 포함한 nested resampling(within-design 게이트와 동일 한계).

## 3) T1 통계 게이트 (winner vs 현 baseline)
# 승격 검증 리포트 (T1 게이트)

- folds: 50 (repeated K-fold, paired)
- winner 실패 fold: 0 / baseline 실패 fold: 0

| 모델 | 평균 fold MAE |
|---|---|
| naive | 9.8383 |
| baseline | 2.4755 |
| winner | 2.9223 |

**winner vs baseline**: mean_diff=+0.4468 (95% CI [+0.4045, +0.4884]), Wilcoxon p=0.000, Cohen's dz=+2.89
**winner vs naive**: mean_diff=-6.9160 (95% CI [-6.9944, -6.8355]), Wilcoxon p=0.000

## verdict (winner vs baseline): **worse**

> ⚠️ 반복 K-fold는 train/val 중첩으로 fold 점수들이 **상관**된다 — bootstrap CI·Wilcoxon p는
> 독립 표본 가정보다 **낙관적**(불확실성 과소평가)일 수 있다. verdict는 보수적으로 해석.

> ⚠️ **단일 설계(n=53) 한계**: 본 검증은 한 설계 내 repeated K-fold일 뿐,
> 일반화(다른 설계 예측)를 주장하지 않는다. held-out *설계* 교차검증은 **T4**의 몫.
> verdict: `distinguishable`일 때만 승격 후보 — auto 모드에선 이후 Codex 심사로 진행, 수동 모드에선 Operator 참고.

## 4) Codex 승격 심사관 (무결성·안전·품질)
- approve: **False**
- 사유: T1 미통과 — 심사 생략

## 5) 승격 규칙
median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).
사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).