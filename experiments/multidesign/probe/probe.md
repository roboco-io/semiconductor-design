# Feature 정규화 probe 리포트 (LODO · naive 기준 사전 고정)

| 스크립트 | aes (held-out) | gcd (held-out) | verdict |
|---|---|---|---|
| naive | 1.7198 | 1.4117 | (기준) |
| winner | 2.7393 | 2.5122 | — |
| baseline | 3.0486 | 2.4424 | — |
| v1_delta | 1.0824 | 1.5723 | partial |
| v2_groupstat | 2.9646 | 2.9837 | not_transferable |
| v3_ratio | 2.6892 | 2.0682 | not_transferable |

> ⚠️ 설계 2개 → 2 fold 저표본 — 방향성 probe(통계 검정 불가).
> 판정 규칙은 결과 확인 전 spec §5에 고정됨(post-hoc 기준 이동 금지, gen-002 교훈).

---

## Operator 해석 (2026-06-11 실측)

- **sanity**: naive·winner·baseline 행이 2026-06-10 crossdesign.md와 소수 4자리까지 일치 — 전 과정 결정성 확인.
- **V1(델타 label) = 유일한 생존 축, partial**: held-out aes에서 **1.0824 — naive(1.7198)를 37% 이김**
  (교차설계에서 naive를 이긴 첫 모델). 게다가 훈련 데이터가 gcd 53행뿐인 상태의 성과. held-out gcd에선
  1.5723으로 naive(1.4117)에 못 미치나 winner(2.5122)보단 훨씬 낫다. → label 오프셋 제거가 분포 shift
  대응의 지배적 축이라는 방향 신호.
- **비대칭 관찰**: gcd(53행, tight)→aes 전이는 성공, aes(691행, loose)→gcd는 부분 실패. 작은 쪽으로의
  전이가 더 어렵다 — 설계 다양성(제3 설계)의 가치를 시사.
- **V2(설계별 표준화) 실패 — 단 해석 caveat**: 표준화된 num_stages가 0을 지나며 사본의
  `add_timing_features` per-stage 비율 feature가 노이즈화(코드 리뷰 발견)되는 교란이 섞여 있어,
  "축 자체가 죽었다"고 단정하기엔 과적. label 오프셋도 미해결이라 이중 불리.
- **V3(무차원 비율) 실패 — 역시 caveat**: 절대 앵커(synth_slack ns)가 feature에서 사라져 naive조차
  표현 불가한 구조. gcd held-out에서 winner보다 개선(2.07 vs 2.51)된 건 스케일 제거의 부분 효과.
  또한 num_stages·pg 코드는 비-무차원으로 남아 완전한 scale-free는 아님.
- **후속 매핑(spec §5)**: `transferable` 0개·`partial` 1개 — "전부 실패"도 "확정 성공"도 아닌 중간.
  실질 함의: ① V1을 기본 축으로 한 조합(V1×V3, V1+제3설계)이 다음 후보 ② ibex 추가는 V1 축
  검증(3-fold) 관점에서 가치 상승 — 단 비용 결정은 별도 브리프로.
