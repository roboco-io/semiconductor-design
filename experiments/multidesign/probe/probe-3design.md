# Feature 정규화 probe 리포트 (LODO · naive 기준 사전 고정)

| 스크립트 | aes (held-out) | gcd (held-out) | ibex (held-out) | verdict |
|---|---|---|---|---|
| naive | 1.7198 | 1.4117 | 12.8071 | (기준) |
| winner | 2.6795 | 2.5208 | 2.9618 | — |
| baseline | 2.9228 | 2.4503 | 2.9841 | — |
| v1_delta | 1.0809 | 1.5312 | 6.4387 | partial |

> ⚠️ 설계 3개 → 3 fold 저표본 — 방향성 probe(통계 검정 불가).
> 판정 규칙은 결과 확인 전 spec §5에 고정됨(post-hoc 기준 이동 금지, gen-002 교훈).

---

## Operator 해석 (2026-06-11, 3설계 3-fold — ibex 추가)

- **입력**: gcd 53(−1.37~0) + aes 691(+0.44~+2.93) + ibex 2040(+1.49~+8.23) = 2,784행.
  3-fold LODO — **훈련 fold에 처음으로 2설계 혼합**(2-fold에선 단일설계 훈련뿐이었음).
- **발견 1 — 혼합 분포 훈련이 절대 모델 전이를 살린다**: held-out ibex에서 winner 2.96 vs
  naive 12.81(**4.3× 격파**). 어제 "모든 학습 모델이 naive 이하"(2-fold) 결론은 *단일설계 훈련*의
  한계였음이 부분 반증 — 설계 수가 늘면 절대 스케일 모델도 전이 시작. (단 aes/gcd held-out에선
  여전히 naive에 패배 — 훈련 2설계가 해당 held-out 분포를 안 덮는 경우.)
- **발견 2 — V1(델타)의 적용 한계**: ibex는 synth→route 드리프트 자체가 거대(naive MAE 12.8 =
  델타 평균 크기). 훈련 설계(gcd/aes)의 델타 분포(~1.4-1.7)와 자릿수가 달라 **델타도 분포 밖
  외삽이 되면 약함**(V1 6.44 — naive보단 2× 낫지만 winner 2.96에 패배). 잔차 학습은 "드리프트가
  설계 간 안정적"일 때의 무기.
- **종합 — 단일 정답 축 없음**: held-out별 최선이 갈림(aes→V1 1.08 / gcd→naive 1.41 /
  ibex→winner 2.96). verdict `partial`(V1, 2/3) 유지. 교차설계 일반화는 "축 하나"가 아니라
  설계 특성 조건부 — 다음 단계는 Operator 수동 조합이 아니라 **루프 환류**(에이전트가 이 trade-off를
  탐색, 게이트는 3-fold LODO)가 자연스러움.
- **sanity**: aes/gcd 열의 naive 값이 2-fold 실측과 동일(1.7198/1.4117 — fold 구성이 같아 일치 정상).
  winner/baseline 값은 훈련셋이 2설계로 늘어 2-fold 수치와 다름(예: winner aes 2.74→2.68) — 설계대로.
