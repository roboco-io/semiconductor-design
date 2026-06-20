# gen-007 리포트 (자율 승격 게이트)

**최종 결정: rejected_t1**  ·  winner: `cand-002`

> ⚠️ 다설계 dataset 평가 — val_mae를 gen-001~003과 직접 비교 금지(설계 교체).

## 1) 후보 순위 (median val_mae, 낮을수록 좋음)
| 후보 | sdk | 전략 | median_val_mae |
|---|---|---|---|
| cand-002 ⭐ | claude | aggressive | 1.2929 |
| cand-001 | codex | moderate | 2.4029 |
| cand-003 | codex | conservative | 3.8016 |
| cand-000 | claude | conservative | 3.9417 |

## 2) 교차설계 LODO 게이트 (held-out 설계 일반화)
# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)

**verdict: generalizes_better**  ·  winner 우세 설계: 2/3  ·  평균 격차(winner−baseline): +0.6922

| 설계(held-out) | naive | baseline | winner | 검증 |
|---|---|---|---|---|
| aes | 1.7198 | 2.6795 | 1.2766 | ✅ |
| gcd | 1.4117 | 2.5208 | 2.0368 | ✅ |
| ibex | 12.8071 | 2.9618 | 6.9254 | ✅ |

> ⚠️ **저표본**: 설계 3개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지
> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을
> 포함한 nested resampling(within-design 게이트와 동일 한계).

## 3) T1 통계 게이트 (winner vs 현 baseline)
# 승격 검증 리포트 (교차설계 T1 · repeated LODO)

- folds: 30 (설계 3개 × repeats 10, leave-one-design-out, paired)
- winner 실패 fold: 0 / baseline 실패 fold: 0

| 모델 | 평균 fold MAE |
|---|---|
| naive | 5.3129 |
| baseline | 3.7975 |
| winner | 4.1575 |

**winner vs baseline**: mean_diff=+0.3600 (95% CI [-0.8207, +1.5510]), Wilcoxon p=0.655, Cohen's dz=+0.10
**winner vs naive**: mean_diff=-1.1554 (95% CI [-2.0914, -0.3071]), Wilcoxon p=0.184

## verdict (winner vs baseline): **indistinguishable**

> ⚠️ **반복-상관**: 같은 held-out 설계를 repeats번 반복한 fold들은 동일 val set을 공유해
> **상관**된다 — 독립 표본이 아니므로 bootstrap CI·Wilcoxon p는 독립 가정보다 **낙관적**
> (불확실성 과소평가)이다. verdict는 보수적으로 해석.

> ⚠️ **저표본**: 설계 3개뿐 → 교차설계 표본이 근본적으로 작다. 강한 일반화
> 결론은 설계 확보(Sub-A) 후에야 가능 — 현 verdict는 *방향성에 가까운* 통계 신호.

> verdict: `distinguishable`일 때만 승격 후보 — auto 모드에선 이후 Codex 심사로 진행, 수동 모드에선 Operator 참고.

## 4) Codex 승격 심사관 (무결성·안전·품질)
- approve: **False**
- 사유: T1 미통과 — 심사 생략

## 5) 승격 규칙
median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).
사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).