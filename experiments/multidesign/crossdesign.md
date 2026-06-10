# 교차설계 일반화 리포트 (held-out 설계 LODO · 방향성 probe)

**verdict: mixed**  ·  winner 우세 설계: 1/2  ·  평균 격차(winner−baseline): -0.1197

| 설계(held-out) | naive | baseline | winner | 검증 |
|---|---|---|---|---|
| aes | 1.7198 | 3.0486 | 2.7393 | ✅ |
| gcd | 1.4117 | 2.4424 | 2.5122 | ✅ |

> ⚠️ **저표본**: 설계 2개 → **통계 검정 불가**. 이건 일반화 *probe*(경향)이지
> 유의성 주장이 아니다. 설계 더 확보(Sub-A) 시 강한 결론 가능. 또한 train.py 내부 분할을
> 포함한 nested resampling(within-design 게이트와 동일 한계).

---

## Operator 해석 (2026-06-10, 첫 실측)

- **입력**: gcd 53행(slack −1.37~0, tight) + aes 691행(+0.44~+2.93, loose) → LODO 2 fold.
  winner = gen-001 승격 train.py, baseline = pre-gen-001(사람, `619e24f~1`).
- **헤드라인**: verdict `mixed`(1승 1패)이지만 진짜 발견은 **둘 다 naive(항등 예측:
  synth_slack = post_route_slack, 훈련 데이터 미사용)보다 크게 나쁘다**는 것. within-design
  MAE ~0.10–0.15였던 모델들이 미관측 설계에선 2.5–3.0으로 **~20× 붕괴**. 분포가 정반대인
  설계로는 *어떤* 학습 모델도 전이되지 않았다 — 결정 브리프의 시나리오 1(분포 shift 지배,
  정직한 negative) 그대로.
- **해석 주의**: naive는 훈련 데이터를 전혀 안 써 분포 shift에 *면역*이고, 학습 모델은 feature가
  절대 ns 스케일(synth_slack_ns 등)이라 훈련 설계의 slack 범위 밖 설계에선 순수 외삽이 된다.
  naive가 이기는 건 "모델이 무의미"가 아니라 "이 feature 표현으로는 cross-design 외삽이 안
  된다"는 신호 — 설계 정규화(상대 slack·clock 주기 비율 등) 또는 분포가 겹치는 훈련 설계
  혼합이 필요함을 시사.
- **함의(ibex 결정에)**: 단순히 설계 *수*를 늘리는 것(3-fold)보다, ① 훈련 fold에 양/음 slack이
  섞이는 구성 ② feature 정규화가 선행 후보. ibex run-task는 이 재평가 후 결정.
- **기계 검증**: `run_crossdesign_gate`가 합성 fixture 밖 *실데이터*에서 정상 작동(2 fold 모두
  valid, 작업물 tempdir 격리) — Sub-B 기계의 실측 첫 가동 확인.
