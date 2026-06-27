# 논문 Outline — AutoResearch for EDA Surrogate Models: 자율 루프가 재현한 교차설계 일반화의 벽

> created: 2026-06-27 · status: draft outline
> 성격: **negative-result + process novelty** 논문의 골격. experiments/README + gen-001~008 +
> 게이트 진화 + co-evolution을 컴파일. 각 절에 *repo 출처*를 매핑해 "컴파일"임을 명시(발명 아님).
> 정합: [`INTENT.md`](../INTENT.md) Learnings, [`README.md`](../README.md), Perplexity grounded 출처.

---

## 0. 제목 후보

1. *"In-distribution Optimization ≠ Cross-design Generalization: An Autonomous-Research Case Study on EDA Timing Surrogates"*
2. *"비전문가가 운전하는 자율 연구 루프 — EDA surrogate에서 교차설계 일반화의 벽을 재현하다"*
3. *"권력분립 게이트가 막은 다섯 번의 위양성: AutoResearch를 EDA surrogate에 적용한 negative-result 보고"*

→ 1번(영문, 발견 중심) 권장. 부제로 process/accessibility 축 병기.

## 1. Abstract (초안)

> EDA surrogate 모델(합성 직후 feature → 최종 PPA/timing 예측)의 *모델 탐색 루프*는 기계적이지만
> 여전히 사람이 수작업한다. 우리는 Karpathy의 **AutoResearch**(연구를 검색으로 환원하는 population
> 진화 루프)를 EDA surrogate 학습에 **처음** 적용하고, 비전문가 Operator가 *방향만* 잡아 8세대를
> 자율 진화시켰다. 핵심 산출은 *더 나은 모델*이 아니라 **정직한 negative result**다: in-loop
> `val_mae`는 세대마다 최저를 경신했으나(gen-007 1.29 → gen-008 0.53), 교차설계 일반화는 5세대 내내
> 통계적으로 구별 불가(`indistinguishable`)였다. 즉 *분포 내 최적화와 미관측 설계 일반화는 구조적으로
> 분리*된다 — 이는 ML-for-EDA에서 *이미 알려진* 현상이며, 본 연구의 기여는 (1) 자율 루프가 이를
> **스스로 재현**했고, (2) **생성자≠판정자 4단 객관 게이트**(median→LODO→교차설계 T1→Codex)가
> 5건의 위양성 승격을 차단했으며, (3) 비전문가가 per-winner 승인 없이 자율 루프를 *이해·조종*했다는
> **프로세스/접근성** 축에 있다. 승격 0건은 실패가 아니라 게이트가 작동한 증거다. 전 과정·코드·
> 데이터를 오픈소스로 공개한다.

> ✅ **contribution claim 정렬됨(2026-06-28)**: Abstract·§3의 기여(2 방어·3 발견·4 접근성)는
> [`INTENT.md`](../INTENT.md) 품질기준의 **negative-result 성공 기준 3조건(방어·발견·접근성)**과 1:1
> 대응한다. "달성"은 H-A positive가 아니라 이 셋의 동시 충족.

## 2. Introduction

- **동기**: surrogate ML-for-EDA는 성숙(CircuitNet 2.0·RouteNet·Net2·MasterRTL·Circuit-as-Points)하나,
  모델 구조·하이퍼파라미터·feature 탐색 *루프*는 사람이 수작업 — 이 루프는 기계적이다.
- **갭**: AutoResearch(karpathy)는 이 루프를 자동화했으나 대상은 *LLM 학습*. **EDA surrogate 적용 사례 부재.**
- **본 연구의 차별 축**: 기술 substrate가 아니라 (a) *비전문가 empowerment + 이해가능성*(접근성),
  (b) *정직한 negative result*(교차설계 벽의 자율 재현 + 게이트의 위양성 차단).
- **기여 목록** (§아래) → 출처: [`INTENT.md`](../INTENT.md) Why, [`README.md`](../README.md) "무엇을, 왜".

## 3. 기여 (Contributions)

1. **AutoResearch를 EDA surrogate에 첫 적용** — 단일 `train.py` 변형·고정 예산·population+median 선택.
2. **권력분립 4단 자동 게이트** — median→LODO→교차설계 T1→Codex(생성자≠판정자). gen-002~008에서
   **5건의 위양성 승격 차단**을 실증. 게이트가 *스스로 진화*(단일 seed→median→LODO→교차설계 T1).
3. **정직한 negative result** — "in-loop val_mae↓ ≠ 교차설계 일반화"를 자율 루프가 5세대에 걸쳐 재현.
   이것이 ML-for-EDA의 *알려진* 현상임을 grounded로 명시(과대주장 회피).
4. **비전문가 empowerment + co-evolution** — 비전문가가 방향(`program.md`)·튜토리얼만으로 자율 루프를
   조종. Operator 학습 ↔ 프로젝트 진화의 양방향 순환을 날짜별로 문서화.

## 4. Background & Related Work

- **EDA flow 기초**: RTL→GDSII(합성·P&R·STA), 타이밍 슬랙·PPA·routability. 오픈소스(OpenROAD/Yosys).
- **ML-for-EDA surrogate**: RouteNet·Net2·CircuitNet 2.0·MasterRTL·Circuit-as-a-Set-of-Points. (SNS는 미인용 — grounded 미검증.)
- **AutoResearch & 진화적 ML 탐색**: 연구=검색, 단일 train.py·고정 예산·git ratchet; population-based training 계보.
- **교차설계 일반화 & 분포 shift**: *알려진 현상* — SwiftCTS(OOD/LODO), EDALearn(전이성 벤치마크),
  robustness(1% 셀 이동 → 예측 90% 변동). → **본 연구의 negative result를 이 문맥에 위치**시킨다.
- 출처: §11 References(Perplexity citation 검증). 개념 해설은 [`tutorial/`](../tutorial/) 01~04 레슨.

## 5. System / Method

- **frozen substrate**: `prepare.py`(데이터·평가 프로토콜) — 에이전트 변경 금지, 공정 비교 보장.
- **변형 대상**: `train.py` 단일 파일 — 신규 의존성 금지, 고정 학습 예산(AutoResearch 제약 계승).
- **진화 루프**(`src/pipeline/`): candidate_gen(Claude+Codex) → runner(5 seed) → median 선택 → 게이트.
- **4단 게이트**(생성자≠판정자): ① median(5-seed) ② LODO(설계 단위 방향성) ③ 교차설계 T1(repeated
  leave-one-design-out + Wilcoxon, 통계 유의) ④ Codex(누수·gaming 코드 리뷰).
- **Operator-in-loop**: per-winner 승인 아님. 방향(`program.md`) + 튜토리얼식 리포트로 큰 흐름 이해.
- 출처: [`wiki/gate-chain.md`](../wiki/gate-chain.md), [`docs/TRAIN.md`](TRAIN.md),
  [`docs/superpowers/specs/`](superpowers/specs/) (median harness·T1·교차설계 T1 설계).

## 6. Experimental Setup

- **데이터셋**: 진짜 ORFS flow(AWS Fargate)로 4설계 확보 — gcd 53 + aes 691 + ibex 2040 + jpeg 4410
  = **7194행**. `DATASET.flow_lockfile_sha`로 재현성 앵커. (jpeg 61% 지배는 §8에서 중요.)
- **지표**: path slack 예측 MAE(ns), 낮을수록 좋음. baseline = naive(합성 slack=최종 slack) + 사람 train.py.
- **게이트 임계값**: 설계 spec 소유(INTENT-vs-spec invariant) — 논문은 *인용*만, 재정의 금지.
- 출처: [`experiments/real-*-fargate/`](../experiments/), [`issues/001~006`](../issues/), INTENT Learnings 2026-06-06·06-21c.

## 7. Results (세대별 컴파일)

| 세대 | 시험한 것 | 결과 | 게이트가 잡은 것 / 발견 |
|---|---|---|---|
| gen-001 | 에이전트 vs 사람 baseline | **승격** | H-A 엄밀 재확증(winner 0.148 vs 0.194, dz=−1.27, p<0.001) — *within-design 한정* |
| gen-002 | 단일 seed 선택 | reject | 단일 seed 1등이 5-seed median 꼴찌(위양성) → median 도입 |
| gen-003 | 엄밀 채점 첫 세대 | rejected_codex | Codex가 검증셋 cherry-pick(평가 누수) 적발 — T1은 속았으나 코드 리뷰가 차단 |
| gen-004~005 | 다설계 혼합 + LODO | rejected_lodo | median-winner가 미관측 설계서 baseline 후퇴(2세대 연속) |
| gen-006 | program.md 힌트 강화 | rejected_t1 | LODO 통과↔혼합 T1 충돌 → T1을 *교차설계* 통계 게이트로 재정의 |
| gen-007 | 새 4단 체인 첫 세대 | rejected_t1 | 역대 최저 median(1.29)+LODO 통과인데 교차설계 T1 indistinguishable(ibex 패배) |
| gen-008 | 4설계(+jpeg) | rejected_t1 | median 0.53(역대 최저)·4설계 2:2 무승부 → indistinguishable, jpeg 편향 확인 |

- **핵심 그래프**(이미 제작): [`tutorial/assets/the-wall.svg`](../tutorial/assets/the-wall.svg) — in-loop
  val_mae 하강 vs 교차설계 T1 평탄.
- 출처: 각 [`experiments/gen-NNN/README.md`](../experiments/README.md)·`report.md`, INTENT Learnings(날짜별).

## 8. Discussion

- **구조적 분리**: in-distribution 최적화(val_mae↓)와 교차설계 일반화는 다른 능력 — 5세대 견고.
- **게이트의 가치 = 위양성 차단**: median만 믿었다면 5번 baseline 오염. 게이트의 가치는 *통과시킬 때*가
  아니라 *낙관적 지표에 속지 않을 때* 증명된다.
- **알려진 현상의 자율 재현**(정직성): 본 결과는 신규 발견이 아니라 SwiftCTS·EDALearn 류가 보고한
  현상을 *사람이 설계하지 않은 자율 루프*가 수렴해 재현한 것. 기여는 "발견"이 아니라 "재현+포착".
- **co-evolution**: 운영 마찰(gen-002 위양성·gen-006 게이트 충돌)이 평가 프로토콜을 진화시키고, 진화한
  프로토콜이 결론을 단단히 함. Operator 학습 ↔ 프로젝트 진화의 양방향. 출처: INTENT Learnings 전체.
- **jpeg 편향**: 최대 설계(61%)가 학습 지배 → 가까운 분포 전이만 개선. 다음 지렛대를 시사.

## 9. Limitations

- **저표본 설계 수**(4) — LODO/T1 통계력 제한. 더 많은 설계가 필요(EDALearn 류).
- **jpeg 61% 편향** — 설계 균형 미적용.
- **auto-gate 미구현** — 전환 중. Operator가 게이트 리포트 확인 후 머지(임시 단계).
- **단일 PDK/flow**(sky130/ORFS) — 공정·노드 간 전이 미검증.
- **surrogate ≠ sign-off** — 근사 예측, functional correctness 주장 아님(INTENT Not).

## 10. Conclusion & Future Work

- 결론: 자율 연구 루프 + 객관 게이트가 *정직한 negative result*를 산출 — 양적 개선(재추첨·데이터 추가)으로는
  벽을 못 넘는다.
- Future: **질적 전환**(설계-불변 표현 명시 유도) 또는 **설계 균형 sampling**(jpeg 편향 완화).
  → 열린 결정 [`issues/007`](../issues/007-gen-009-next-experiment-direction.md)(gen-009 지렛대 A/B/C/D).
- (연기) reasoning trace 증거 평면 — 이해가능성 강화 2차 세대.

## 11. Reproducibility & References

- **재현성**: 오픈소스(OpenROAD/Yosys), repo 공개, `flow_lockfile_sha` 앵커, 게이트 코드+123 tests.
- **References** (Perplexity citation 검증, 2026-06-24):
  - OpenROAD: https://en.wikipedia.org/wiki/OpenROAD_Project
  - CircuitNet 2.0(ICLR24): https://openreview.net/pdf/18243659a4c68baa73e34792453c17d63e6f68a3.pdf
  - Xie ML-for-EDA survey: https://arxiv.org/abs/2206.03032v1
  - MasterRTL(ICCAD23): https://arxiv.org/abs/2311.08441
  - Circuit as a Set of Points(NeurIPS23): https://proceedings.neurips.cc/paper_files/paper/2023/file/6697bb267dc517379bc8aa326e844f8d-Paper-Conference.pdf
  - AutoResearch 해설: https://www.verdent.ai/guides/what-is-autoresearch-karpathy · https://www.snackonai.com/p/autoresearch-the-engineering-behind-karpathy-s-autonomous-ml-experiment-loop
  - 교차설계 일반화: https://zhiyaoxie.com/files/chapter_route.pdf · SwiftCTS https://arxiv.org/pdf/2606.11348v1.pdf · NSF robustness https://par.nsf.gov/servlets/purl/10626479 · EDALearn https://arxiv.org/pdf/2312.01674.pdf

---

## 부록 A — 컴파일 출처 매핑 (이 outline은 발명이 아니라 재구성)

| 절 | 1차 출처 |
|---|---|
| Abstract·§3 기여 | [`INTENT.md`](../INTENT.md) Why/Learnings, [`README.md`](../README.md) |
| §4 Background | Perplexity grounded 브리핑(§11 References), [`tutorial/`](../tutorial/) 01~04 |
| §5 Method | [`wiki/gate-chain.md`](../wiki/gate-chain.md), [`docs/superpowers/specs/`](superpowers/specs/), [`docs/TRAIN.md`](TRAIN.md) |
| §7 Results | [`experiments/README.md`](../experiments/README.md) + gen-001~008 `README.md`/`report.md`, INTENT Learnings |
| §8 Discussion | INTENT Learnings 2026-06-07~06-24, [`docs/TUTORIAL.md`](TUTORIAL.md) §6.5 |
| §10 Future | [`issues/007`](../issues/007-gen-009-next-experiment-direction.md) |

## 부록 B — 미해결(논문 확정 전 필요)

1. ~~성공 기준 한 줄 — INTENT `TODO(human)` 확정~~ ✅ **완료(2026-06-28)**: 3조건 결합형(방어·발견·접근성)으로 확정, Abstract/§3 정렬.
2. **정량 게이트 임계값** — 설계 spec에서 nail down(INTENT-vs-spec invariant) 후 §6에 인용.
3. **타깃 venue** — workshop(negative-result/ML-for-EDA) vs arXiv 선공개. 분량·형식 결정.
