# gen-008 리포트 (자율 승격 게이트)

**최종 결정: rejected_t1**  ·  winner: `cand-001`

> ⚠️ 다설계 dataset 평가 — val_mae를 gen-001~003과 직접 비교 금지(설계 교체).

## 1) 후보 순위 (median val_mae, 낮을수록 좋음)
| 후보 | sdk | 전략 | median_val_mae |
|---|---|---|---|
| cand-001 ⭐ | codex | moderate | 0.5258 |
| cand-000 | claude | conservative | 1.2834 |
| cand-002 | claude | aggressive | 1.3072 |
| cand-003 | codex | conservative | 1.3277 |

## 2) 교차설계 LODO 게이트 (held-out 설계 일반화)
# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)

**verdict: mixed**  ·  winner 우세 설계: 2/4  ·  평균 격차(winner−baseline): -0.0420

| 설계(held-out) | naive | baseline | winner | 검증 |
|---|---|---|---|---|
| aes | 1.7198 | 2.5151 | 1.0657 | ✅ |
| gcd | 1.4117 | 3.0008 | 3.3849 | ✅ |
| ibex | 12.8071 | 2.9650 | 3.9842 | ✅ |
| jpeg | 0.5694 | 0.5282 | 0.4066 | ✅ |

> ⚠️ **저표본**: 설계 4개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지
> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을
> 포함한 nested resampling(within-design 게이트와 동일 한계).

## 3) T1 통계 게이트 (winner vs 현 baseline)
# 승격 검증 리포트 (교차설계 T1 · repeated LODO)

- folds: 40 (설계 4개 × repeats 10, leave-one-design-out, paired)
- winner 실패 fold: 0 / baseline 실패 fold: 0

| 모델 | 평균 fold MAE |
|---|---|
| naive | 4.1270 |
| baseline | 2.2233 |
| winner | 2.2417 |

**winner vs baseline**: mean_diff=+0.0184 (95% CI [-0.2907, +0.3202]), Wilcoxon p=0.666, Cohen's dz=+0.02
**winner vs naive**: mean_diff=-1.8853 (95% CI [-3.0932, -0.7466]), Wilcoxon p=0.087

## verdict (winner vs baseline): **indistinguishable**

> ⚠️ **반복-상관**: 같은 held-out 설계를 repeats번 반복한 fold들은 동일 val set을 공유해
> **상관**된다 — 독립 표본이 아니므로 bootstrap CI·Wilcoxon p는 독립 가정보다 **낙관적**
> (불확실성 과소평가)이다. verdict는 보수적으로 해석.

> ⚠️ **저표본**: 설계 4개뿐 → 교차설계 표본이 근본적으로 작다. 강한 일반화
> 결론은 설계 확보(Sub-A) 후에야 가능 — 현 verdict는 *방향성에 가까운* 통계 신호.

> verdict: `distinguishable`일 때만 승격 후보 — auto 모드에선 이후 Codex 심사로 진행, 수동 모드에선 Operator 참고.

## 4) Codex 승격 심사관 (무결성·안전·품질)
- approve: **False**
- 사유: T1 미통과 — 심사 생략

## 5) 승격 규칙
median 선택 → LODO 통과 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).
사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).