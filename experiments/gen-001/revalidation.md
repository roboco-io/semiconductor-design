# gen-001 소급 재심 (T1 승격 검증 게이트)

- **재심일**: 2026-06-08
- **게이트**: `run_validation_gate`, repeated 5-fold ×10 (50 fold, paired), n_boot=10000.
  설계 [T1 spec](../../docs/superpowers/specs/2026-06-07-t1-promotion-validation-gate-design.md).
- **목적**: gen-001 H-A("에이전트가 사람 baseline 능가")가 단일 seed 점추정이 아닌
  **엄밀 paired 통계**로도 유지되는지 재확인. (gen-002 위양성 발견의 후속 — 같은 의심을 gen-001에도 적용.)
- **대상**: winner = 현 `train.py`(gen-001 winner, Codex feature-eng+앙상블) ·
  baseline = pre-gen-001 `train.py`(사람 작성, git `619e24f~1`) · naive(합성 슬랙=최종 슬랙).

## 결과

| 모델 | 평균 fold MAE (50 fold) |
|---|---|
| naive | 1.4138 |
| baseline (pre-gen-001, 사람) | 0.1943 |
| **winner (gen-001, 에이전트)** | **0.1476** |

- **winner vs baseline**: mean_diff = **−0.0466**, 95% CI **[−0.0567, −0.0365]**(0 미포함),
  Wilcoxon **p < 0.001**, **Cohen's dz = −1.27**(큰 효과). 실패 fold 0/0.
- **winner vs naive**: mean_diff = −1.2661, 95% CI [−1.3343, −1.1990], p < 0.001.
- **verdict (winner vs baseline): `distinguishable`** — 에이전트 winner가 사람 baseline을
  통계적으로 유의하게 능가.

## 해석

- **H-A 엄밀 재확증**: gen-001의 "에이전트가 baseline 능가"는 단일 seed 우연이 아니라,
  50 fold paired에서 CI가 0을 넘지 않고 큰 효과크기(dz=−1.27)로 유지된다. **gen-001 승격은 정당했다.**
- **gen-002와 모순 아님**: gen-001(사람→에이전트)은 0.194→0.148의 *큰 도약*이라 robust.
  gen-002(이미 좋은 winner→미세 개선)는 53샘플 노이즈에 묻힌 *작은 차이*였다. T1 게이트가
  "진짜 도약"과 "노이즈 속 미세조정"을 구분한다 — 게이트의 설계 목적이 실증됨.
- **한계(불변)**: 단일 설계(n=53) 내 검증일 뿐, 다른 설계로의 일반화는 주장하지 않는다.
  held-out *설계* 교차검증은 **T4**의 몫.

## 상태

- gen-001 `generation.json` status `promoted` **유지**(재심이 승격을 지지). 변경 없음.
- 본 재심은 advisory. 기록은 Operator 승인(2026-06-08) 하에 커밋.
