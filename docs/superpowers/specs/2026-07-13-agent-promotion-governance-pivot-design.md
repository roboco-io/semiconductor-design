# 피벗 설계 — 에이전트 산출물 자동 승격 거버넌스의 도메인-불문 일반성 실증

> date: 2026-07-13 · status: **draft — Codex 검토 게이트 대기**
> 결정 경로: [issues/008-pivot-direction.md](../../../issues/008-pivot-direction.md) (Operator가 A 선택)
> 선행 spec: [2026-05-29 피벗](2026-05-29-autoresearch-eda-surrogate-pivot-design.md) ·
> [2026-07-02 v2 재설계](2026-07-02-frozen-encoder-representation-redesign-design.md) — 이후 **사례 연구 1 lineage**로 지위 변경
> 본 spec이 채택되면 THE active 설계 spec.

## §1 배경과 결정 경로

surrogate v2 사이클이 encoder 채택 게이트 2회 기각으로 종결(INTENT Learnings 2026-07-10)된 뒤,
Operator가 "실제 프로덕션 레벨 가치" 평가를 요청했다. 평가 결론: EDA surrogate 모델 자체는
프로덕션 가치가 없다(교차설계 7세대 연속 기각, 4설계 7,194행 규모). 실질 가치는 **4단 게이트
권력분립이 자율 루프의 위양성 승격 6건+을 차단한 작동 사례** — 즉 "LLM 에이전트 산출물을 사람
개입 없이 언제 믿고 승격하나"라는 도메인-불문 거버넌스 문제의 실증에 있다. Operator가 피벗을
지시했고, decision brief(issue 008) 4선택지 중 **A(거버넌스 일반화)**를 선택했다.

### 브레인스토밍 Q&A (2026-07-12~13, 결정 확정 순)

| # | 질문 | Operator 결정 |
|---|---|---|
| 1 | 1차 산출물(제품)은? | **2차 도메인 실증 먼저** — 추출/라이브러리화는 실증 후 |
| 2 | 실증 도메인은? | **복수: 알고리즘 성능 최적화 + LLM 프롬프트 진화** |
| 3 | 리포 전략은? | **이 리포 증축** (v2 선례 — 삭제가 아니라 증축, co-evolution 이력 보존) |
| 4 | 기존 novelty 축 처리는? | **메타 목적(의도공학·co-evolution)·튜토리얼 유지, "비전문가 empowerment" 헤드라인은 "신뢰가능한 자율(게이트 거버넌스)"로 교체** |
| 5 | 실행 접근은? | **순차 실증 + 최소 어댑터** (도메인 A 먼저, 통과 후 B; 추출은 별도 사이클) |

### 사전 조사 — 게이트 코드 결합도 (Explore, 2026-07-12)

- 통계 코어(`paired_comparison`·`verdict`·`fold_splits`·`design_fold_splits`,
  `src/pipeline/validation.py`)는 **100% 도메인-중립**.
- 도메인 결합 지점은 4곳으로 국지화: ① metric 키명(`val_mae` — runner.py:45 파싱),
  ② naive baseline 계산(`synth_slack_ns`/`post_route_slack_ns` — validation.py:42),
  ③ group 추출(`group_key`), ④ 후보 실행 CLI 계약(train.py `--data/--out/--seed`).
- 전체 파이프라인 LOC 기준 재작성 필요분 ~43%, 그러나 **어댑터 콜백 4개 교체만으로 새 도메인
  실증 시작 가능** — "실증 먼저" 결정과 정합.

## §2 Why

**헤드라인**: *자율 에이전트가 생성한 산출물을 사람 개입 없이 언제 믿고 승격할 수 있는가* —
EDA 사례에서 실증된 4단 게이트 권력분립(median 선발 → LOGO 일반화 probe → 사전 고정 paired
통계 검정 → 독립 엔진 의미 심사)이 **도메인-불문 거버넌스 패턴임을 실증**한다.

**문제**: 에이전트 진화 루프는 산출물을 스스로 승격해야 하지만 in-loop 지표는 위양성·gaming에
구조적으로 취약하다. 본 리포 EDA 사이클의 실증: 단일 seed 위양성(gen-002), 검증셋 선택
gaming(gen-003, T1을 구조적으로 속임), 교차설계 일반화 착시(gen-004~008 5세대). 그러나 이
실증은 단일 도메인 한정 — 게이트가 EDA 데이터 구조에 우연히 맞았을 가능성을 배제 못 한다.

**가설 (판정 지향 — yes/no 어느 쪽이든 산출물, 2026-06-24 negative-result 프레이밍 계승)**:
- **H-G1 (게이트 일반성)**: 같은 4단 게이트가 지표 의미가 전혀 다른 도메인(실행시간, eval
  점수)에서도 위양성 승격을 차단하고 정당 승격만 통과시킨다.
- **H-G2 (발견의 일반성)**: "in-loop 지표 개선 ≠ 교차그룹 일반화"(EDA 5세대 재현)가 에이전트
  진화 루프의 일반 패턴인가 — 재현되면 일반 발견으로 격상, 안 되면 "도메인 조건부"라는 더
  정밀한 발견.

**메타 목적 유지**: (1) 의도공학 사례 연구, (2) Operator 학습 ↔ 프로젝트 진화 co-evolution.
피벗 2회의 INTENT 이력 자체가 증거 평면. 튜토리얼식 이해가능성은 "신뢰가능한 자율"의 구성
요소로 재배치(자율을 신뢰하려면 사람이 큰 흐름을 검사 가능해야 함).

## §3 Grounded Positioning (2026-07-12 조사, citation 31건)

개별 요소는 전부 존재하나 **3중 결합의 조립은 부재**:

| 요소 | 기존 영역 (붐빔) | 갭 |
|---|---|---|
| champion/challenger 승격 게이트 | MLflow·Vertex·SageMaker 표준 관행 | 통계 검정 없는 단순 지표 비교. "자동 승격"과 "엄밀 통계"가 각각 존재하나 결합 드묾 |
| 생성 엔진 ≠ 심사 엔진 | 2026년 평가 실무 상식 (self-preference bias 정량화) | **자동 머지 게이트의 구조적 요건(거부권)으로 정식화한 사례 없음** |
| reward hacking 탐지 | METR·TRACE·RHB 벤치마크 급성장 | 벤치마크·분류기 연구 단계 — 진화 루프에 플러그인하는 승격 게이트 도구 없음 |
| pre-registration | 임상·심리학 표준 | 진화 루프 결합은 arXiv 2606.29119 1편(승격 아닌 사전 스크리닝) |

**가장 가까운 경쟁자**: AlphaEvolve evaluation cascade(다단이나 비통계·단일 엔진 계열),
MLE-bench GPT-4o 로그 심사(게이트가 아닌 사후 감사).

**정직성 요건**: TRACE 기준 LLM 심사자의 gaming 탐지율은 ~63% — **Codex 관문도 불완전함을
명시**하고, 게이트 체인은 "완벽한 방어"가 아니라 "위양성 비용을 낮추는 다층 방어"로 주장한다.

**후순위 기회**: RHB/RewardHackingAgents 벤치마크로 각 관문의 기여를 ablation — 도메인 A·B
실증 이후 후보로만 기록(범위 통제).

조사 원문(URL 31건)은 부록 A.

## §4 What — 도메인 A: 알고리즘 성능 최적화 루프

기존 4-step 루프(Candidate Generation → Batch Launch → Result Collection → Selection)와
게이트 체인을 그대로 재사용하고, 어댑터 콜백 4개만 교체한다.

| 축 | EDA 사이클 (사례 연구 1) | 도메인 A |
|---|---|---|
| 에이전트 변형 대상 | `train.py` 단일 파일 | `domains/algo-opt/solver.py` 단일 파일 |
| 지표 | `val_mae` (낮을수록 좋음) | 벤치마크 실행시간 중앙값 (낮을수록 좋음) |
| 정합성 전제 | (해당 없음 — 회귀 태스크) | **정합성 테스트 통과 필수** — 오답 후보는 지표 무효(inf 처리, 도태) |
| 그룹(`group_key`) | 설계 (gcd/aes/ibex/jpeg) | 워크로드 패밀리 (입력 크기·분포 유형별 벤치 그룹) |
| naive baseline | 항등 예측 | 원본(사람 작성) 참조 구현 |
| LODO/LOGO | leave-one-design-out | leave-one-workload-family-out |
| T1 fold | seed × K-fold | 워크로드 × 반복 측정 (타이밍 noise를 paired 통계가 흡수) |
| Codex 심사 표적 | leakage·post-selection bias | 벤치 입력 하드코딩·결과 캐싱·측정 조작·정합성 테스트 우회 |
| frozen 자산 | `prepare.py`·`pretrain/` | **벤치마크 스위트 + 측정 하니스** (에이전트 변경 금지, 가드 차단) |
| 실행 환경 | AWS Fargate/Spot | **로컬** — AWS 비용 0, 세대당 분 단위 |

**어댑터 인터페이스** (콜백 4개 — 기존 코드는 수정 최소화, 어댑터 층에서 주입):
1. `parse_metric(stdout) -> float` — 후보 실행 결과에서 지표 추출
2. `naive_metric(rows) -> float` — 참조 구현의 fold별 지표
3. `extract_group(row) -> str` — 워크로드 패밀리 키
4. `run_candidate(candidate_path, bench_path, out_dir, seed)` — 후보 실행 계약

**알고리즘 태스크 선정**: gaming 여지가 풍부한 휴리스틱 계열(bin packing, 정규식 매칭,
그래프 휴리스틱 등)에서 1개 — **issue 009로 분리, 구현 plan 전 확정**. 선정 기준:
① 정합성 판정이 결정적, ② 워크로드 패밀리 4개+ 구성 가능, ③ 단일 파일 구현이 수백 줄 이내,
④ 실행시간이 로컬에서 초 단위.

**세대 운영**: N=5세대, 세대당 후보 4개(기존 config 관례), 각 후보 5-seed 아날로그
(측정 반복 5회) median 선발. 세대 완료마다 `experiments/algo-gen-NNN/README.md` 튜토리얼
필수(기존 마무리 단계 유지).

**도메인 B (LLM 프롬프트 진화)**: 도메인 A 판정 완료 후 **별도 spec**으로 착수. 본 spec은
범위에 포함하지 않는다.

## §5 판정 질문 — 사전 고정 (결과 확인 후 변경 금지)

### H-G1 판정 (게이트 일반성)

5세대 실행 후 다음을 **모두** 충족하면 1차 실증 성립:

- **(부당 승격 0건)** 승격된 모든 후보가 사후 감사를 통과. "부당 승격" = 다음 중 하나라도
  해당: ① 정합성 테스트 위반이 사후 발견, ② frozen 하니스 변조, ③ 수동 감사에서 Codex가
  놓친 gaming 발견, ④ **예비 감사 패밀리**(루프·게이트에 전혀 노출하지 않은 신선한 워크로드
  패밀리 1개, 실행 전 봉인)에서 naive(참조 구현) 대비 유의 열세.
- **(판정 근거 완비)** 모든 승격/기각 판정에 근거 artifact(generation.json, T1 리포트,
  Codex verdict)가 커밋되어 사후 검사 가능.
- **(기각의 정당성)** 기각된 후보 중 최소 1건 이상에서 기각 사유가 실재함을 사후 감사로
  확인(게이트가 "전부 기각"으로 안전빵 하는 퇴화 방지 — 단, 5세대 모두 정당 기각이면 그
  자체가 유효 판정).

임계값·통계 파라미터는 기존 코드 관례를 **복사 인용**한다(재정의 금지): T1 α=0.05,
bootstrap n=10,000, Wilcoxon + 95% CI + Cohen's dz, LOGO 부분 실패(`n_valid < n_groups`) 시
차단.

### H-G2 판정 (발견의 일반성)

세대별로 "in-loop 지표(median 실행시간) 개선"과 "LOGO/T1 교차그룹 verdict"의 괴리 여부를
기록한다. 5세대 중 3세대 이상에서 in-loop 최저 후보가 교차그룹 `indistinguishable`/`worse`이면
EDA 발견의 재현(일반 패턴 지지), 아니면 도메인 조건부 발견으로 기록. **어느 쪽이든 산출물.**

## §6 Not

**절대 금지**:
- **맹목적 자율 금지** (유지): 객관적 게이트 + 튜토리얼식 이해가능성 없는 자율 진행 금지.
- **사후 기준 변경 금지** (v2 교훈 격상): §5의 판정 질문·감사 기준은 결과 확인 전 고정.
  변경은 새 spec의 brainstorming→Codex 게이트로만.
- **생성 엔진 = 심사 엔진 금지** (신규 명문화): 의미 심사는 생성자와 다른 엔진. 근거:
  self-preference bias 정량 연구(부록 A [17][21]).
- **frozen 자산 에이전트 변경 금지**: 도메인 A 벤치마크 스위트·측정 하니스. 기존 EDA frozen
  목록(`prepare.py`·`pretrain/`·`models/encoder-v1.pt`)도 사례 연구 보존 차원에서 유지.
- **정합성 우회 금지**: 정합성 테스트 미통과 후보의 성능 수치는 무효.

**기술 제약** (유지): Python 3.12/uv, ruff 100자 py312, 에이전트는 단일 파일만 변형·신규
의존성 설치 금지·고정 예산, 루프 LLM은 구독 CLI만(metered API 금지), direct commit to main.

**범위 밖**:
- 라이브러리 추출·패키징 — 두 도메인 실증 완료 전 금지.
- 도메인 B 착수 — 도메인 A 판정 완료 전 금지.
- RHB/reward-hacking 벤치마크 ablation — A·B 이후 후보로만 기록.
- EDA gen-009 — 종결된 v1 사이클 재개 안 함(별도 Operator 결정 없이는).
- SOTA 알고리즘 성능 주장 — 목표는 거버넌스 실증.

## §7 리포 구조·마이그레이션

```
semiconductor-design/            # 리포명 유지 (rename은 필요 시 후속 결정)
├── INTENT.md                    # Why/What/Not 재작성, Learnings 전량 보존
├── domains/algo-opt/            # 신설 — solver.py·벤치 스위트·어댑터·정합성 테스트
├── src/pipeline/                # 게이트 체인 유지 — 어댑터 주입점만 추가
├── prepare.py, train.py, pretrain/, experiments/gen-00N/  # 사례 연구 1로 동결 유지
├── experiments/algo-gen-NNN/    # 도메인 A 세대 리포트 + 튜토리얼
└── issues/009-...               # 알고리즘 태스크 선정 등 열린 결정
```

**문서 정합**:
- INTENT.md: 본 spec §2·§4·§6 반영, status `exploring` 유지, Learnings에 2026-07-13 피벗 기록.
- CLAUDE.md·PRD.md: 헤드라인·구조 갱신(EDA = 사례 연구 1). 4-엔티티 ERD는 도메인-중립 유지,
  DATASET 개념을 "도메인 벤치 스위트"로 일반화.
- issues/008 → resolved.

**하우스키핑** (피벗 커밋에 포함):
- `.handoff.md` 삭제(구 사이클 handoff 대체).
- untracked 산출물 삭제: `experiments/*/dataset-v2/`, `experiments/multidesign/dataset-v2-4design.jsonl`,
  `models/train.{log,pid,stdout.log}` — 기각 encoder 기반, 재생성 가능.

## §8 성공 기준 요약과 후속

- **성공** = §5의 H-G1·H-G2 판정이 사전 고정 기준대로 내려지고, 근거 artifact와 튜토리얼로
  비전문 독자가 흐름을 따라갈 수 있음. 판정 방향(승격/기각, 재현/비재현)은 성공 여부와 무관.
- **후속 순서**: 본 spec Codex 게이트 → Operator 리뷰 → INTENT/CLAUDE/PRD 정합 커밋 →
  issue 009(태스크 선정) → 어댑터·벤치 구현 plan(`writing-plans`) → 도메인 A 5세대 →
  판정 → 도메인 B spec.

## 부록 A — Positioning 조사 URL (2026-07-12, grounded, citation 31건)

1. https://www.datasops.com/blog/mlops-cicd-model-deployment
2. https://medium.com/@artur.fejklowicz/zero-touch-ml-model-promotion-building-a-fully-automated-champion-challenger-pipeline-on-google-aa0bb5cfc854
3. https://mlflow.org/docs/latest/ml/model-registry/
4. https://medium.com/google-cloud/decision-gate-for-mlops-pipelines-with-vertex-ai-experiments-73d5b258928e
5. https://stacksimplify.com/blog/ml-governance-model-registry/
6. https://datarekha.com/interview/mlops/model-registry-safely-promote-to-production/
7. https://ideas.paasup.io/global/mlops-pipeline-en/
8. https://engineersofai.com/docs/mlops/model-registry/model-staging-and-promotion
9. https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/
10. https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/AlphaEvolve.pdf
11. https://www.nature.com/articles/s41586-026-10265-5
12. https://sakana.ai/ai-scientist-nature/
13. https://arxiv.org/html/2502.14297v3
14. https://www.deeplearning.ai/the-batch/openais-mle-bench-tests-ai-coding-agents
15. https://github.com/openai/mle-bench
16. https://arxiv.org/html/2605.18747v1
17. https://vadim.blog/llm-as-judge/
18. https://futureagi.com/blog/llm-as-judge-best-practices-2026/
19. https://futureagi.com/blog/llm-as-a-judge/
20. https://www.adaline.ai/blog/llm-as-a-judge-reliability-bias
21. http://www.arxiv.org/pdf/2504.03846.pdf
22. https://arxiv.org/html/2605.21748v1
23. https://cs224r.stanford.edu/spring_2025/projects/pdfs/CS224R_Final_Report%20(1)1.pdf
24. https://metr.org/blog/2025-06-05-recent-reward-hacking/
25. https://zylos.ai/research/2026-06-07-specification-gaming-reward-hacking-ai-agents/
26. https://arxiv.org/html/2603.11337
27. https://arxiv.org/html/2601.20103v1
28. https://arxiv.org/pdf/2605.02964.pdf
29. https://arxiv.org/html/2604.13602v1
30. https://arxiv.org/pdf/2606.29119.pdf
31. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.LeaveOneGroupOut.html
