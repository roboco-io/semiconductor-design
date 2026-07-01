# in-distribution 최적화 ≠ 교차설계 일반화: EDA 타이밍 surrogate에 대한 자율 연구 사례

**저자:** (작성 시 기입) · **상태:** arXiv preprint 초안 (2026-06-30) · **형식:** Markdown
**코드·데이터:** https://github.com/roboco-io/semiconductor-design (오픈소스)

> 영문본: [`PAPER.md`](PAPER.md). 이 문서는 그 한국어 번역본이다. 세대 통계는 저장소의
> `experiments/gen-NNN/` 리포트와 [`INTENT.md`](../INTENT.md) Learnings에서, 외부 주장은 인용
> 문헌(§11)에서 가져왔다.

---

## 초록 (Abstract)

EDA **surrogate** 모델—합성 직후 feature로 칩의 최종 timing/PPA를 예측하는 모델—의 *모델 탐색
루프*는 기계적이지만 여전히 사람이 손으로 돌린다. 우리는 Karpathy의 **AutoResearch**(단일 학습
스크립트를 고정 예산으로 변형하고 지표가 개선될 때만 유지하는 자율 "연구=검색" 루프)를 EDA
타이밍-슬랙 surrogate 학습에 **처음** 적용하고, **비전문가 operator**가 개별 winner를 승인하는 대신
*방향* 수준에서 8세대를 조종하게 했다(완전 자동 승격이 설계 목표이며, 현 임시 단계에선 operator가 각
게이트 리포트를 확인한 뒤 머지하고, 초기 세대는 이 재프레이밍 이전이다). 핵심 결과는 더 나은 모델이
아니라 **정직한 negative result**다: in-loop 검증 오차(`val_mae`)는 세대마다 역대 최저를 경신했지만
(gen-007 1.29 → gen-008 0.53 ns; 단 gen-8 median은 확장된 4설계 dataset 기준이라 직접 비교 불가),
어느 세대도 게이트를 통과한 교차설계 승리를 내지 못했다—최종 교차설계 검정으로 판정된 두 세대(7·8)는
baseline과 *통계적으로 구별 불가*였고, 그 이전 세대는 상류에서 기각됐다. 즉 *in-distribution
최적화와 미관측 설계 일반화는 구조적으로 분리*된다—이는 ML-for-EDA에서 이미 문서화된 현상이다.
따라서 우리의 기여는 **프로세스·접근성** 축에 있다: (1) 자율 루프가 *모델 변경을 사람이 직접
설계하지 않고도* 이 알려진 벽을 *재현*했고, (2) 4단 **권력분립 게이트**(median → leave-one-design-out → 교차설계 통계 검정 → 독립
코드 리뷰)가 gen-002~008의 모든 승격 시도를 각기 다른 사유로 차단하고 baseline 무결성을 지켰으며, (3) 비전문가가 문서화된
방향과 튜토리얼식 리포트로 루프를 조종했다. 승격 0건은 실패가 아니라 게이트가 작동했다는 증거다.
모든 코드·데이터·전체 세대 이력을 오픈소스로 공개한다.

---

## 1. 서론

ML-for-EDA는 성숙한 분야다: surrogate 모델은 초기 단계 정보로 routability·IR-drop·wirelength·
timing을 예측해, 전체 sign-off flow의 긴 실행시간을 절약한다 [1,2,4,5]. 그러나 *외부 루프*—모델
구조·하이퍼파라미터·feature 설계 선택—는 여전히 사람이 수작업으로 반복한다. 그 루프는 기계적이다:
변형하고, 한 숫자를 재고, 유지하거나 버린다.

Karpathy의 **AutoResearch** [8,9]는 "연구"를 "검색"으로 환원해 바로 이 루프를 자동화한다: 코딩
에이전트가 단일 `train.py`를 반복 변형하고, 고정 예산으로 학습한 뒤, 단일 검증 지표를 재고, 개선
됐을 때만 commit한다(아니면 revert)—한 방향 래칫(ratchet). AutoResearch는 *LLM* 학습을 대상으로
하며 무인 자율("사람은 자고 있어도 된다")을 전제한다. **EDA surrogate 학습에 적용된 적은 없다.**

우리는 그 갭을 메운다. 단 차별 축은 기술 substrate가 아니다. (a) **비전문가 empowerment +
이해가능성**—비전문가가 방향과 큰 흐름의 이해만으로 자율 루프를 전문영역으로 조종할 수 있는가?—
그리고 (b) **정직한 negative result**: 루프가 알려진 일반화 벽을 자율적으로 재현했고, 그 과정의
위양성을 객관적 게이트가 잡았다는 것이다.

**기여.**
1. **AutoResearch를 EDA surrogate 학습에 첫 적용**(단일 `train.py` 변형, 고정 예산, population +
   median 선택).
2. **4단 권력분립 게이트**(median → LODO → 교차설계 T1 → 독립 Codex 리뷰)가 gen-002~008의 모든 승격
   시도를 각기 다른 사유(단일 seed 운·평가 누수·교차설계 후퇴·winner가 노출한 게이트 정합오류)로
   차단하고 세대를 거치며 *스스로 진화*.
3. **정직한 negative result**: "in-loop `val_mae` ↓ ≠ 교차설계 일반화"를 자율 루프가 여러 세대에
   걸쳐 재현(최종 교차설계 검정으로 판정된 gen-007/008에서 가장 뚜렷)하고, 이를 새 발견이 아니라
   *알려진* ML-for-EDA 현상으로 명시적으로 위치시킴.
4. **비전문가 empowerment와 co-evolution**: 비전문가 operator가 방향과 튜토리얼로 루프를 조종;
   operator 학습 ↔ 프로젝트 진화의 순환을 날짜별로 문서화.

## 2. 배경 및 관련 연구

**RTL-to-GDSII와 타이밍 슬랙.** 칩은 RTL(Verilog)에서 합성(Yosys)·배치배선(OpenROAD)·STA
(OpenSTA)를 거쳐 GDSII 레이아웃으로 컴파일된다 [1]. 여기서 관심 대상은 **타이밍 슬랙**: 신호의
required time과 arrival time 사이 마진(양수=클럭 충족, 음수=너무 느림)이다. 우리는 *합성 직후*
feature로 *최종*(라우팅 후) 슬랙을 예측한다.

**ML-for-EDA surrogate.** RouteNet은 배치 feature로 routability·DRC 핫스팟을 예측하고 [2], Net2는
그래프 구조로 net wirelength를, CircuitNet 2.0은 routability·IR-drop·timing용 공개 데이터셋
(20k+ 샘플)이며 [4], MasterRTL은 비트수준 연산 그래프로 합성 *이전* PPA를 [5], "Circuit as a Set
of Points"는 배치를 점 구름으로 보아 혼잡도·DRC를 예측한다 [6]. 우리 surrogate는 GNN이 아니라 표
형식 트리 앙상블을 쓴다(사유는 저장소 참고).

**AutoResearch와 진화적 ML 탐색.** AutoResearch [8,9]는 단일 학습 스크립트를 고정 예산으로 변형
하고 git-ratchet accept/revert 규칙을 쓰며, population-based training·블랙박스 최적화의 계보에
있으나, 미리 정한 공간이 아니라 *코드 공간*에서 개방적으로 탐색한다.

**교차설계 일반화와 분포 shift.** ML-for-EDA 모델이 미관측/분포 밖 설계에서 성능이 저하되는 것은
*잘 문서화된* 사실이다 [10,11]; LODO(leave-one-design-out)와 zero-shot OOD 검정이 표준 프로토콜이며;
혼잡도 예측기는 1% 셀 이동에 최대 90%까지 출렁이고 [12]; EDALearn 같은 벤치마크가 교차설계·교차노드
전이성을 잰다 [13]. **우리의 negative result는 정확히 이 문헌 안에 위치한다**: 현상 자체의 novelty를
주장하지 않고, 그 *자율 재현과 포착*만을 주장한다.

## 3. 시스템 및 방법

시스템은 **frozen substrate**와 **변형 대상 스크립트**를 분리한다:

- **`prepare.py` (frozen).** STA 리포트에서 feature+label 데이터셋을 만들고 평가 프로토콜을 정의한다.
  에이전트는 이를 **변경할 수 없다**—모든 후보가 동일 데이터·동일 규칙으로 판정되도록 보장한다.
- **`train.py` (변형 대상, 단일 파일).** 에이전트의 유일한 대상. 신규 의존성 금지, 고정 학습 예산
  (AutoResearch 제약 계승).
- **진화 루프 (`src/pipeline/`).** 세대당: `candidate_gen`(Claude·Codex가 각각 변형 제안) →
  `runner`(각 후보를 5 seed로 학습) → **median** 선택(최저 median `val_mae`가 winner) → 게이트.

**4단 권력분립 게이트** (생성자 ≠ 판정자). winner는 넷을 *모두* 통과해야 하며, 하나라도 막히면
baseline 유지:

1. **median (5-seed):** 단일 split의 운을 배제.
2. **LODO (leave-one-design-out):** 설계 하나를 통째로 빼고, winner가 *더 많은* held-out 설계에서
   baseline을 이기는지 본다(*방향성* probe).
3. **교차설계 T1:** leave-one-design-out을 seed에 걸쳐 반복하고 paired Wilcoxon 검정 + bootstrap
   신뢰구간을 적용—방향성 격차가 *통계적으로 유의*한지 묻는다.
4. **Codex 리뷰:** *다른* LLM이 후보 코드를 읽어, 통계가 못 보는 평가 누수·metric gaming을 잡는다.

정량 통계 임계값은 설계 spec 소유다; 본 논문은 관측값을 인용할 뿐 임계값을 정의하지 않는다.
**Operator-in-loop:** 설계 목표는 operator가 개별 winner를 승인하는 대신 방향(`program.md`)을 정하고
각 세대를 튜토리얼식 리포트로 따라가는 것이다. 현 임시 단계(auto-gate 미구현, §7)에선 operator가
게이트 리포트를 확인한 뒤 여전히 머지하며, 초기 세대(1–2)는 이 재프레이밍 이전으로 operator 승인/거절이
있었다.

## 4. 실험 설정

**데이터셋.** 진짜 ORFS flow(AWS Fargate 실행)로 네 설계를 확보: gcd(53행)·aes(691)·ibex(2040)·
jpeg(4410)를 합쳐 **7194행** 데이터셋. `flow_lockfile_sha`가 재현성을 앵커한다. jpeg 단독이 전체의
약 61%인 점은 §6에서 중요해진다.

**지표와 baseline.** path-slack 예측 MAE(ns, 낮을수록 좋음). baseline: *naive* 예측기(합성 슬랙을
최종 슬랙으로 사용) + 사람이 작성한 `train.py`.

## 5. 결과

여덟 세대 요약(통계는 세대별 리포트에서):

| 세대 | 시험한 것 | 결과 | 게이트가 잡은 것 / 발견 |
|---|---|---|---|
| 1 | 에이전트 vs 사람 baseline | **승격** | H-A를 *within-design*서 확증: winner 0.148 vs 사람 0.194 ns, dz = −1.27, p < 0.001 (naive = 1.41) |
| 2 | 단일 seed 선택 | 미승격 | 단일 seed winner(0.0992)가 median *꼴찌*; 직전 baseline(0.0865)이 최저 → median harness 도입 |
| 3 | 엄밀 채점 | rejected_codex | Codex가 검증셋 cherry-pick(post-selection 누수)을 적발 — 통계 게이트는 속았음 |
| 4–5 | 다설계 혼합 + LODO | rejected_lodo | median-best winner가 held-out 설계에서 2세대 연속 후퇴 |
| 6 | 생성 힌트 강화 | rejected_t1 | 첫 LODO 통과, 그러나 혼합-fold T1은 *worse* → LODO↔T1 충돌 노출; T1을 교차설계 검정으로 재정의 |
| 7 | 새 4단 체인 | rejected_t1 | 역대 최저 median(1.29)·LODO 통과인데 교차설계 T1 indistinguishable(mean diff +0.36, p = 0.655, dz = 0.10); ibex서 패배 |
| 8 | 4번째 설계(jpeg) | rejected_t1 | 역대 최저 median(0.53), 4설계 2–2 무승부 → indistinguishable(mean diff +0.018, p = 0.666); jpeg 편향 확인 |

**벽.** gen-004~008에서 in-loop median `val_mae`는 역대 최저를 경신했으나(단 gen-008의 median은 확장된
4설계 dataset 기준이라 직접 비교 불가), 어느 winner도 게이트를 통과한 교차설계 승리를 내지 못했다.
기각 메커니즘은 세대마다 달랐다: gen-004/005는 앞단 LODO에서 막혀 T1에 도달하지 못했고; gen-006은
LODO↔T1 충돌을 노출해 T1을 교차설계 검정으로 재정의하게 만들었으며(그 소급 교차설계 재평가는 실은
*distinguishable*이었고, 이것이 재정의를 촉발); gen-007·gen-008—최종 교차설계 T1으로 판정된 두
세대—은 역대 최저 median에도 둘 다 *indistinguishable*이었다. 핵심 그림(저장소
`tutorial/assets/the-wall.svg`)이 하강하는 in-loop 곡선과 평탄한 교차설계 결과를 대비한다.

## 6. 논의

**구조적 분리.** in-distribution 검증 오차를 낮추는 것과 미관측 설계로 일반화하는 것은 *다른
능력*이다. 이는 연이은 세대, 세 가지 선택 지렛대(데이터 추가·힌트 강화·4번째 설계), 두 에이전트
계열에 걸쳐 성립했다.

**게이트의 가치 = 위양성 차단.** median만 믿었다면, 일반화하지 못한 역대 최저 winner들(gen-004/005는
held-out 설계서 후퇴, gen-007/008은 교차설계 indistinguishable)과 gen-002의 단일-seed 위양성이
baseline을 오염시켰을 것이다; gen-006은 다른 경우로, 일반화 실패가 아니라 자기 winner가 노출한 게이트
정합오류로 막혔다. 게이트는 승격할 때가 아니라, 낙관적 in-loop 숫자에 속기를 거부할 때
그 가치를 증명한다. gen-003이 가장 날카롭다: 한 후보가 *검증 fold 자체에서* 최선 모델을 골라
(dz = −1.51로 통계 게이트를 속임), 오직 독립 코드 리뷰어만이 이를 차단했다.

**알려진 현상의 자율 재현(정직성).** 우리 발견은 새 과학이 아니라 SwiftCTS [11]·EDALearn [13]이
보고한 것을 재진술한다. 루프와 게이트는 사람이 설계·진화시켰다; 사람이 직접 설계하지 않은 것은
*후보 궤적*이며, 그것이 그 루프 아래서 이 벽에 수렴했고 게이트가 위양성을 포착했다. 기여는 발견이
아니라 재현-플러스-포착이다.

**co-evolution.** 운영 마찰이 방법을 이끌었다: 위양성(gen-002)이 median harness를, LODO↔T1 모순
(gen-006)이 교차설계 통계 게이트를 낳았다. 각 수정이 결론을 더 단단히 했다—operator 학습 ↔ 프로젝트
진화, 양방향.

**jpeg 편향.** 최대 설계(61%)가 학습을 지배해, winner는 가까운 분포 전이만 개선했다—다음 지렛대를
곧장 가리킨다.

## 7. 한계

- **적은 설계 수(4)** — LODO/T1 통계력 제한; 더 많은 설계 필요.
- **jpeg 지배(61%)** — 설계 균형 sampling 미적용.
- **auto-gate 미구현**: 현재 operator가 게이트 리포트 확인 후 머지(임시 단계). 설계 의도는 완전
  자동 승격.
- **단일 PDK/flow**(sky130/ORFS) — 교차노드 전이 미검증.
- **surrogate ≠ sign-off**: 근사 예측이며 functional correctness를 주장하지 않는다.

## 8. 결론 및 향후 연구

자율 연구 루프 + 객관적 게이트가 *정직한 negative result*를 산출했다: 양적 조정(재추첨·데이터 추가)
으로는 교차설계 벽을 넘지 못한다. 우리는 **성공**을 에이전트가 일반화서 baseline을 이기는 것이
아니라, 여기서 모두 충족된 세 조건의 결합으로 정의한다: (방어) 게이트가 위양성을 차단하고 baseline
무결성을 유지; (발견) in-loop ≠ 교차설계 분리가 사전 고정 게이트 하에 여러 세대에서 재현; (접근성)
비전문가가 루프를 조종하고 각 판정을 튜토리얼로 따라감.

**향후 연구**: *질적* 전환—설계-불변 표현을 명시적으로 유도—또는 jpeg 편향을 없애는 **설계 균형
sampling**(저장소에 열린 결정으로 추적). 연기된 reasoning-trace 증거 평면은 이해가능성을 더 강화할
것이다.

## 9. 재현성

모든 EDA 도구는 오픈소스(OpenROAD/Yosys); 저장소는 공개; 데이터셋은 `flow_lockfile_sha`로 앵커;
게이트는 123 tests로 커버. 각 세대의 후보·점수·게이트 리포트는 `experiments/`에 커밋돼 있다.

## 10. 감사의 글

이 프로젝트는 반도체 설계 **비전문가의 학습·PoC** 결과물이다; 저장소 면책 조항 참고. 기여와 정정을
환영한다.

## 11. 참고문헌

1. OpenROAD Project. https://en.wikipedia.org/wiki/OpenROAD_Project
2. Z. Xie et al., "Intelligent Circuit Design with ML" (RouteNet, Net2). https://arxiv.org/abs/2206.03032v1
3. OpenROAD-flow-scripts tutorial. https://openroad-flow-scripts.readthedocs.io/en/latest/tutorials/FlowTutorial.html
4. CircuitNet 2.0 (ICLR 2024). https://openreview.net/pdf/18243659a4c68baa73e34792453c17d63e6f68a3.pdf
5. MasterRTL (ICCAD 2023). https://arxiv.org/abs/2311.08441
6. "Circuit as a Set of Points" (NeurIPS 2023). https://proceedings.neurips.cc/paper_files/paper/2023/file/6697bb267dc517379bc8aa326e844f8d-Paper-Conference.pdf
7. CircuitNet dataset. https://circuitnet.github.io
8. AutoResearch — explainer. https://www.verdent.ai/guides/what-is-autoresearch-karpathy
9. AutoResearch — engineering deep-dive. https://www.snackonai.com/p/autoresearch-the-engineering-behind-karpathy-s-autonomous-ml-experiment-loop
10. Z. Xie, "ML Applications in EDA" (cross-design estimator). https://zhiyaoxie.com/files/chapter_route.pdf
11. SwiftCTS (2026, OOD/LODO cross-design). https://arxiv.org/pdf/2606.11348v1.pdf
12. "On Robustness and Generalization of ML-Based EDA" (NSF). https://par.nsf.gov/servlets/purl/10626479
13. EDALearn (cross-design/cross-node transfer benchmark). https://arxiv.org/pdf/2312.01674.pdf
