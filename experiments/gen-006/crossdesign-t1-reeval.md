# gen-006 winner — 교차설계 T1(repeated LODO) 재평가 (2026-06-21)

spec `2026-06-20-crossdesign-t1-gate-design.md` §7 필수 검증. gen-006 winner
(`cand-001`, codex/moderate)를 **새 교차설계 T1 게이트**로 baseline(train.py) 대비 재평가.

| 게이트 | 측정축 | verdict | 통계 |
|---|---|---|---|
| 기존 혼합-T1 (gen-006 실행 시) | in-distribution(혼합 K-fold) | **worse** | mean_diff +0.45, dz +2.89, p≈0 |
| 새 교차설계-T1 (repeated LODO) | 미관측 설계 일반화 | **distinguishable** | mean_diff −0.53, CI[−0.86,−0.23], p=0.003, dz −0.57 |

- fold: 30 (설계 3 × repeats 10, leave-one-design-out, paired).
- **판정이 뒤집힘** — 같은 winner, 정반대 verdict. 두 게이트가 진짜 다른 것을 측정함을 통계로 입증
  (robustness ↔ accuracy 트레이드오프). gen-006의 "stated bar(LODO) ≠ enforced bar(혼합 T1)" 모순 해소.
- 함의: 새 게이트 체인(median → LODO → 교차설계-T1 → Codex)이었다면 gen-006 winner는 LODO
  `generalizes_better` + 교차설계-T1 `distinguishable`로 **승격 후보**였다(Codex 통과 시). program.md
  힌트 강화 효과가 게이트 정합 후 비로소 승격으로 이어질 수 있음.
- 단, 저표본(설계 3개) + 반복-상관 caveat — 강한 결론은 설계 확보(Sub-A) 후.
