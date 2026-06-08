# gen-003 리포트 (자율 승격 게이트)

**최종 결정: rejected_codex**  ·  winner: `cand-001`

## 1) 후보 순위 (median val_mae, 낮을수록 좋음)
| 후보 | sdk | 전략 | median_val_mae |
|---|---|---|---|
| cand-001 ⭐ | codex | moderate | 0.0786 |
| cand-000 | claude | conservative | 0.0803 |

## 2) T1 통계 게이트 (winner vs 현 baseline)
# 승격 검증 리포트 (T1 게이트)

- folds: 50 (repeated K-fold, paired)
- winner 실패 fold: 0 / baseline 실패 fold: 0

| 모델 | 평균 fold MAE |
|---|---|
| naive | 1.4138 |
| baseline | 0.1476 |
| winner | 0.1025 |

**winner vs baseline**: mean_diff=-0.0452 (95% CI [-0.0532, -0.0371]), Wilcoxon p=0.000, Cohen's dz=-1.51
**winner vs naive**: mean_diff=-1.3113 (95% CI [-1.3845, -1.2386]), Wilcoxon p=0.000

## verdict (winner vs baseline): **distinguishable**

> ⚠️ 반복 K-fold는 train/val 중첩으로 fold 점수들이 **상관**된다 — bootstrap CI·Wilcoxon p는
> 독립 표본 가정보다 **낙관적**(불확실성 과소평가)일 수 있다. verdict는 보수적으로 해석.

> ⚠️ **단일 설계(n=53) 한계**: 본 검증은 한 설계 내 repeated K-fold일 뿐,
> 일반화(다른 설계 예측)를 주장하지 않는다. held-out *설계* 교차검증은 **T4**의 몫.
> verdict: `distinguishable`일 때만 승격 후보 — auto 모드에선 이후 Codex 심사로 진행, 수동 모드에선 Operator 참고.

## 3) Codex 승격 심사관 (무결성·안전·품질)
- approve: **False**
- 사유: 동일 validation fold의 MAE를 보고 두 모델 중 best_model을 선택해 val 지표를 최적화한다. 이는 post-selection bias/metric gaming이며 T1 우열을 신뢰하기 어렵다.

## 4) 승격 규칙
median 선택 → T1 `distinguishable` **AND** Codex `approve` → 자동 승격(train.py·tag).
사람은 `program.md` 방향만 — per-winner 승인 없음(2026-06-08 재피벗).