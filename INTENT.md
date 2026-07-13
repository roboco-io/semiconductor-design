# INTENT — 자율 에이전트 산출물 자동 승격 거버넌스 (repo: semiconductor-design)

> status: exploring  (2026-07-13 피벗: EDA surrogate 자동 연구 → 4단 게이트 거버넌스의 도메인-불문 일반성 실증)
> created: 2026-05-10 · pivoted: 2026-05-29(EDA surrogate) · 재피벗: 2026-06-08 · v2 재설계: 2026-07-02 · **피벗: 2026-07-13(거버넌스 일반화)**
> 설계: [`docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md`](docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md) (THE active spec)
> 사례 연구 1(EDA surrogate 8세대 + v2) lineage: [2026-05-29 spec](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md) · [2026-07-02 spec](docs/superpowers/specs/2026-07-02-frozen-encoder-representation-redesign-design.md) · [`PRD.md`](PRD.md)
> 이전 의도(통합 프로그램 3-layer, clarified)는 `archive/integrated-program-3layer` 브랜치에 보존.

## Why

**메타 목적 (세 번째 피벗 후에도 유지)**: (1) 의도공학(intent engineering) 패러다임 우수성의 사례 연구, (2) Operator 학습 ↔ 프로젝트 진화의 co-evolution. 피벗 3회의 본 문서 이력 자체가 증거 평면.

**헤드라인 목표 (2026-07-13 피벗)**: ***자율 에이전트가 생성한 산출물을 사람 개입 없이 언제 믿고 승격할 수 있는가*** — EDA 사례에서 실증된 **4단 게이트 권력분립**(median 선발 → LOGO 일반화 probe → 사전 고정 paired 통계 검정 → 독립 엔진 의미 심사)이 **도메인-불문 거버넌스 패턴임을 실증**한다. 튜토리얼식 이해가능성은 "신뢰가능한 자율"의 구성 요소로 유지(자율을 신뢰하려면 사람이 큰 흐름을 검사 가능해야 함).

**문제**:
- 에이전트 진화 루프는 산출물을 스스로 승격해야 하지만, in-loop 지표는 위양성·gaming에 구조적으로 취약하다. 본 리포의 사례 연구 1(EDA surrogate)이 실증: 단일 seed 위양성(gen-002), 검증셋 선택 gaming(gen-003 — T1 통계 게이트를 구조적으로 속임), 교차설계 일반화 착시(gen-004~008 5세대). 그러나 이 실증은 **단일 도메인 한정** — 게이트가 EDA 데이터 구조에 우연히 맞았을 가능성을 배제 못 한다.
- grounded 조사(2026-07-12, citation 31건 — spec §3·부록 A): champion/challenger 승격 게이트(MLflow·Vertex)는 통계 검정 없는 단순 비교, "생성≠심사 엔진" 원칙은 평가 실무에 확립됐으나 *자동 머지 게이트의 구조적 거부권*으로 정식화된 사례 없음, reward hacking 탐지(METR·TRACE·RHB)는 벤치마크 단계. **"사전 고정 paired 통계 + 교차그룹(LOGO) 관문 + 독립 엔진 의미 심사"의 3중 직렬 결합은 본 조사 범위 내에서 학술·오픈소스·상용 어디에도 조립돼 있지 않다**(가장 가까운 것: AlphaEvolve evaluation cascade, MLE-bench 사후 감사).
- 정직성 요건: LLM 심사자의 gaming 탐지율은 ~63%(TRACE) — 게이트 체인은 "완벽한 방어"가 아니라 **위양성 비용을 낮추는 다층 방어**로만 주장한다.

**가설 (판정 지향 — yes/no 어느 쪽이든 산출물, 2026-06-24 negative-result 프레이밍 계승)**:
- **H-G1 (게이트 일반성)** — 같은 4단 게이트가 지표 의미가 전혀 다른 도메인(실행시간, eval 점수)에서도 위양성 승격을 차단하고 정당 승격만 통과시킨다.
- **H-G2 (발견의 일반성)** — "in-loop 지표 개선 ≠ 교차그룹 일반화"(EDA 5세대 재현 발견)가 에이전트 진화 루프의 일반 패턴인가 — 재현되면 일반 발견으로 격상, 안 되면 "도메인 조건부"라는 더 정밀한 발견.

**확인 방법** (판정 기준은 spec §5에 사전 고정 — 본 문서는 *복사 인용*만):
- 도메인 A(알고리즘 성능 최적화)에 어댑터 4콜백으로 게이트 이식 → **컨트롤 후보 2종**(known-good 승격돼야 함 / known-bad 차단돼야 함, 사전 커밋)으로 민감도 판정 → 자율 5세대 → **사전 등록 사후 감사**(sealed 워크로드 패밀리 포함)로 H-G1 판정, 세대별 괴리 기록으로 H-G2 판정.
- 도메인 A 판정 완료 후 도메인 B(LLM 프롬프트 진화)는 별도 spec으로.
- 구 가설(H-A·H-B)의 판정 결과는 사례 연구 1로 종결 — Learnings 2026-06-24·07-10 참조.

## What

**핵심 기능 (새 사이클 — 도메인 A 실증, spec §4~§5)**:
- [ ] **어댑터 층**: 게이트 체인에 도메인 주입점 4콜백(`parse_metric`·`reference_metric`·`extract_group`·`run_candidate` — 타임아웃·에러 계약 포함). 기존 `src/pipeline` 통계 코어는 무변경.
- [ ] **도메인 A 루프**(`domains/algo-opt/`): 에이전트가 `solver.py` 단일 파일 변형, 지표=벤치 실행시간(정합성 테스트 통과 전제), 그룹=워크로드 패밀리(dev/holdout≥3/sealed 1 분할), LOGO="선발·생성 피드백에 안 쓰인 패밀리"로 재정의. 로컬 실행, AWS 비용 0. (태스크 선정: issue 009.)
- [ ] **컨트롤 후보 2종 사전 등록**: known-good(승격돼야)·known-bad(차단돼야) — 게이트 민감도 판정, 공허 성공(reject-all 퇴화) 차단.
- [ ] **자율 5세대 + 사전 등록 사후 감사**: sealed 패밀리 paired 검정 포함 체크리스트 감사 → H-G1·H-G2 판정. 세대·감사마다 튜토리얼 README 필수.
- [ ] **(후속, 별도 spec)** 도메인 B(LLM 프롬프트 진화) 실증 → 두 실증 후 라이브러리 추출 검토.

**사례 연구 1 (EDA surrogate — 완결, frozen 보존)**:
- [x] 데이터셋 자가생성(`prepare.py`, 4설계 7,194행) · 자율 진화 루프 gen-001~008 · 4단 게이트(median→LODO→교차설계 T1→Codex, gen-002~006 거치며 자가 진화) · 튜토리얼식 세대 리포트.
- [x] v2 frozen encoder 사이클 — 채택 게이트 2회 기각으로 negative result 종결(Learnings 2026-07-10).
- 산출: within-design H-A 확증 + "in-loop val_mae↓ ≠ 교차설계 일반화" 5세대 재현 + 위양성·gaming 차단 6건+ — **새 사이클 가설의 원천 증거**.

**사용자 흐름 (새 사이클)**:
1. Operator가 태스크 서술(program.md 아날로그)·세대 수·패밀리 분할을 spec대로 고정.
2. 컨트롤 후보 2종을 게이트에 투입해 민감도 판정 기록.
3. 에이전트가 `solver.py` 변형 후보 N개 생성 → 게이트 체인이 자동 승격/기각 + 튜토리얼 리포트.
4. 5세대 후 사전 등록 감사 → H-G1·H-G2 판정 → Operator는 판정을 *열람*하고 다음 방향(도메인 B/추출/논문화)을 결정.

**엣지 케이스**:
- 후보가 dev 벤치에 과적합/gaming → holdout LOGO·T1 또는 Codex 의미 심사가 차단 (어느 관문이 잡는지 자체가 데이터).
- 정합성 테스트 실패·타임아웃·크래시 → `valid=false, metric=inf` 도태(게이트 진입 불가).
- 승격 0건 → H-G1은 컨트롤 민감도 항목으로 판정 유지, H-G2는 모수 0이면 `unverifiable` 기록.
- (?) 실행시간 측정 noise의 로컬 환경 변동(CPU 부하) — 반복 측정·paired 설계로 흡수하되 구현 plan에서 고정 절차 확정.

## Not

**절대 금지** (2026-07-13 피벗 spec §6 — 본 문서는 복사 인용):
- **맹목적 자율 금지** (유지): 객관적 게이트 + 튜토리얼식 이해가능성 없는 자율 진행 금지.
- **사후 기준 변경 금지** (v2 교훈 격상): 판정 질문·임계값·감사 기준은 결과 확인 전 spec에 사전 고정. 변경은 새 spec의 brainstorming→Codex 게이트로만.
- **생성 엔진 = 심사 엔진 금지**: 의미 심사는 반드시 생성자와 다른 엔진 (self-preference bias — spec 부록 A [17][21]).
- **frozen 자산 에이전트 변경 금지**: 도메인 A 벤치마크 스위트·측정 하니스·컨트롤 후보·sealed 패밀리 정의. 사례 연구 1 자산(`train.py` B0·`prepare.py`·`pretrain/`·`models/encoder-v1.pt`·커밋된 dataset)도 전량 read-only 유지.
- **정합성 우회 금지**: 정합성 테스트 미통과 후보의 성능 수치는 무효 (오답 빠른 코드는 도태).

**기술 제약**:
- Python 3.12, uv. ruff 100 char, target-version py312.
- 에이전트는 도메인당 단일 파일만 변형(도메인 A: `solver.py`), 신규 의존성 설치 금지, 고정 예산 (AutoResearch 제약 계승).
- 루프 LLM 호출은 구독 CLI(claude/codex)만 — metered API 금지.
- Direct commit to `main` (현재 워크플로).

**범위 밖**:
- **라이브러리 추출·패키징** — 두 도메인 실증 완료 전 착수 금지 ("실증 먼저" 결정의 코드화).
- **도메인 B 착수** — 도메인 A 판정 완료 전 금지 (순차 실행).
- **RHB/reward-hacking 벤치마크 ablation** — A·B 이후 후보로만 기록.
- **EDA gen-009** — 종결된 v1 사이클 재개 안 함 (별도 Operator 결정 없이는).
- **SOTA 알고리즘 성능 주장** — 목표는 거버넌스 실증이지 빠른 알고리즘이 아님.
- 전체 RTL→GDSII 공정 운영 (`archive/integrated-program-3layer`) · 모바일/웹 UI · 다중 사용자.

**품질 기준** (spec §5·§8 복사 인용):
- **실험 완주 성공** = 민감도(컨트롤)·H-G1·H-G2 판정이 *사전 고정 기준대로* 내려지고, 근거 artifact(generation.json·T1 리포트·Codex verdict·감사 README)와 튜토리얼이 커밋됨. **가설 지지 여부는 결과이지 성공 조건이 아님.**
- 자율 자동 승격은 게이트 체인 전 단계 통과 winner만.
- **이해가능성**: 비전문 독자가 각 세대·감사의 큰 흐름을 튜토리얼식 산출물로 따라갈 수 있어야 함.
- 사례 연구 1의 negative-result 성공 기준(방어·발견·접근성 3항, 2026-06-28)은 충족된 채 종결 — Learnings 2026-06-24 참조.

## Learnings

- **2026-07-13** (피벗 3 — EDA surrogate → 게이트 거버넌스 일반화, "프로덕션 가치" 질문이 의도를 재변형) —
  v2 종결 직후 Operator가 "이 프로젝트가 실제 프로덕션 레벨 가치를 제공하는가"를 물었고, 정직한
  평가 결과 *EDA surrogate 자체는 프로덕션 가치 없음*(교차설계 7세대 기각, 4설계 규모) / *실질
  가치는 4단 게이트가 위양성·gaming 승격 6건+을 차단한 거버넌스 작동 사례*라는 결론에 도달 →
  Operator가 decision brief(issue 008) 4선택지 중 **A(거버넌스 일반화)** 선택. 브레인스토밍
  Q&A 5문항(실증 먼저·복수 도메인 순차·리포 증축·empowerment→신뢰가능한 자율 교체·최소 어댑터)
  + grounded positioning 조사(citation 31건 — 3중 결합의 조립 부재 확인, 단 조사 범위 한정 헤지)
  로 spec 확정. **(1) Codex 게이트가 spec의 도메인 전제를 적발**: 1차 심사 block 8건 중 핵심은
  "solver 루프에 LOGO가 무정의"(학습이 없는 도메인에선 fold 격리를 *정보 노출* 기준으로 재정의
  해야 함)와 "승격 0건이어도 통과하는 공허 성공 루프홀"(컨트롤 후보 known-good/known-bad 사전
  등록으로 해소) — 도메인을 옮기자마자 게이트의 숨은 전제가 드러난 것 자체가 일반화 실증이
  필요하다는 피벗 가설의 방증. **(2) 기존 자산의 지위 변경은 삭제가 아니라 재해석**: EDA 8세대
  +v2는 "실패한 목표"에서 "사례 연구 1 = 새 가설의 원천 증거"로 — 코드(통계 코어 100% 중립,
  Explore 실측)·기록·Learnings 전량 보존. **(3) co-evolution**: "성공 재정의"(2026-06-24) →
  "negative result 종결"(07-10) → "그래서 진짜 가치는 무엇인가"(07-12)로 이어진 질문 연쇄가
  의도의 헤드라인 자체를 세 번째로 재변형 — 운영 결과가 아니라 *가치 질문*이 피벗을 촉발한 첫
  사례. status `exploring` 유지. spec:
  [2026-07-13-agent-promotion-governance-pivot-design.md](docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md).

### Learnings (사례 연구 1 — EDA surrogate, 2026-05-29 ~ 2026-07-10)

- **2026-07-10** (v2 encoder 채택 게이트 2회 기각 — 사전 고정 기준이 표현 한계를 노출, 사이클 종결) —
  7설계 코퍼스(18,804 endpoints, 제외 0건)로 graph autoencoder를 2회 사전학습(1차 full-batch,
  2차 mini-batch — Operator 승인 수정)했으나 **선형 probe 게이트(§6.4) 미달로 모두 기각**
  (임베딩만 MAE 1.229→1.157 vs 표형식만 0.418; 재구성·붕괴 진단은 2회 모두 통과).
  **(1) 게이트 정상 작동의 실증**: 결과를 본 뒤 기준을 만지지 않고 기각을 수용 — "약한 표현의
  루프 투입"을 세대 예산 소모 전에 차단. 근거 artifact(`models/encoder-v1.report.json`) 커밋으로
  사후 검사 가능. **(2) 발견**: 라벨(post-route slack)과 준직결인 `synth_slack_ns`가 표형식에
  있는 한, *구조-only* 임베딩이 "임베딩만 ≤ 표형식만" 선형 비교를 이기는 것은 구조적으로 어렵다
  — spec §5 amendment(타이밍 제외)와 §6.4 기준의 조합이 만든 예정된 긴장이며, 올바른 다음 질문은
  단독 성능이 아니라 **한계 효용(표형식+임베딩 ≥ 표형식 단독)**이다. 단 기준 변경은 새 spec의
  사전 고정으로만(사후 튜닝 금지). **(3) 운영 학습**: full-batch(epoch당 1 step)는 patience까지
  28 step — 코퍼스 규모와 무관하게 과소학습(Task 5 리뷰가 예고). 실측 마찰 3건(1_2_yosys.v 경로·
  keep_hierarchy flatten·**출력 포트 per-bit endpoint 명명** — coverage 0.70→1.00)은 전부 합성
  fixture로는 못 잡는 종류였다. **co-evolution**: encoder 기각으로 What의 v2 층은 미충족으로
  남고, 다음 사이클(ablation형 probe)은 brainstorming→Codex 게이트부터 다시. status `exploring` 유지.

- **2026-07-02** (surrogate v2 — frozen encoder 표현 재설계 spec 확정) — 7세대 연속
  `indistinguishable`의 "벽"에 대한 질적 전환 실행 설계를 브레인스토밍(Q&A 6문항) → grounded 조사 →
  Codex 검토 게이트(block 4건 반영 후 approve)로 확정
  ([spec](docs/superpowers/specs/2026-07-02-frozen-encoder-representation-redesign-design.md)).
  **(1) grounded 조사가 당초 결정을 반증**: 브레인스토밍서 택한 "CircuitNet 2.0 하이브리드"가
  조사 결과 라벨 불일치(net delay ≠ endpoint slack)·단면 불일치(post-placement ≠ 합성 직후)·
  도메인 갭 미검증(AdaTimer가 naive 전이 실패 실증)으로 기각 → **자가생성 self-supervised graph
  autoencoder 사전학습**(PreRoutGNN 근거)으로 수정 — "지식 기반 우선" 원칙이 설계 오류를 착수 전에
  잡은 사례. **(2) frozen 경계의 확장**: prepare.py에 더해 encoder(사람 1회 학습, SHA 앵커)도
  frozen 자산 — 루프는 head만 탐색, 공정 비교 보장 논리 동일. **(3) 판정 지향 성공 정의**:
  사전 고정 게이트로 "새 winner가 B0 대비 교차설계 T1 `distinguishable`인가"를 판정 — yes면 질적
  전환이 벽을 넘음(H-A′ 지지), no면 "표현 전환으로도 못 넘는 벽"이라는 더 강한 negative result.
  어느 쪽이든 성공(2026-06-24 negative-result 프레이밍의 직접 연장). **(4) 리포 유지 + 무손실 보존**:
  main은 삭제가 아니라 증축(v1 기록이 B0 비교 대상), 재설계 직전 상태는
  `archive/surrogate-v1-8gen` 브랜치로 보존. **co-evolution**: "발견으로의 수렴"(2026-06-24)이
  다음 사이클의 실험 설계 자체를 판정 지향으로 변형 — 의도의 성공 정의 재정의가 spec 구조
  (§7 판정 질문 사전 고정)로 물질화. status `exploring` 유지.

- **2026-06-24** (프레이밍 확정 — '달성'을 H-A positive에서 negative result로 재정의) — 리뷰 결과
  gen-002~008 **7세대 연속 reject**로 교차설계 H-A는 미달이나, 이는 본 프로젝트의 진단(in-loop
  val_mae↓ ≠ 교차설계 일반화)이 5세대째 견고함을 뜻한다. Operator가 '성공'을 *에이전트가 더 나은
  surrogate 생산(H-A positive)*이 아니라 **프로세스 novelty + co-evolution + 정직한 negative result**
  로 재정의. 함의: 추가 세대(재추첨·데이터 추가)는 Learnings 2026-06-21d가 예고한 대로 이 벽을 못
  넘으므로, 동력을 *루프 반복*에서 **8세대 기록의 정합·컴파일(논문화)**로 전환. H-A는 *within-design
  확증 / 교차설계는 구조적 분리 발견*으로 정직하게 범위 한정. **co-evolution**: '범위 과대' 마찰
  (2026-05-29 피벗)에 이어 이번엔 '가설 미달'이라는 운영 결과가 의도의 *성공 정의 자체*를 재변형 —
  승격 0건이 실패가 아니라 게이트가 5건의 위양성을 막은 증거라는 reframe이 핵심. status `exploring`
  유지(구현으로의 수렴이 아니라 *발견으로의 수렴*).

- **2026-06-21d** (gen-008 — 4설계 첫 세대, 세 지렛대 정렬 후에도 무승부 → "val_mae↓ ≠ 교차설계 우위"
  견고) — Sub-A(데이터)·힌트(생성)·게이트(판정) 세 지렛대를 모두 당긴 뒤 첫 세대. winner cand-001
  val_mae **0.53**(gen-007 1.29→계속 최저 경신)·LODO mixed(우세 2/4)·교차설계 T1 40 fold. **결과**:
  winner vs baseline 평균 fold MAE 2.24 vs 2.22(mean_diff +0.018, p=0.666) → `indistinguishable` →
  `rejected_t1`. **(1) jpeg 편향 부분 확인**: winner가 jpeg(0.41 vs 0.53)·aes(1.07 vs 2.52)서 우세,
  gcd·ibex(jpeg과 먼 분포)서 열세 — jpeg(61% 비중)이 학습 지배해 *가까운 분포* 전이만 개선. 혼합훈련
  회복과 jpeg 편향이 공존. **(2) 정직한 무승부**: 4설계로 승패 2:2 → 통계적으로 winner가 baseline을
  전반적으로 못 능가. 4 fold가 됐어도 "전반 우위 없음"을 게이트가 정확히 판정. **(3) 핵심 발견 5세대째
  견고**: median val_mae는 gen-007(1.29)→gen-008(0.53) 계속 낮아지나 교차설계 T1은 줄곧 indistinguishable.
  **in-loop 지표 개선 ≠ 교차설계 일반화 우위** — 이게 본 프로젝트가 5세대 자율 진화로 축적한 가장 견고한
  실증. 함의: 단순 재추첨·데이터 추가로는 이 벽을 못 넘음. 다음 지렛대는 *생성 전략의 질적 전환*(예:
  설계-불변 표현을 명시 유도) 또는 *설계 균형*(jpeg 비중 완화 sampling)일 가능성. negative result가
  "in-distribution 최적화와 교차설계 일반화의 구조적 분리"라는 일반화 가능한 발견으로 수렴.

- **2026-06-21c** (Sub-A 완료 — jpeg 4번째 설계 확보, LODO/T1 3→4 fold) — 네 세대(gen-004~007)가
  일관되게 가리킨 근본 병목(저표본 설계 3 + ibex 단독 의존)을 해소. AWS Fargate로 jpeg ORFS flow를
  native x86 완주(~50분, exitCode 0, DRT 다수 iteration 후 violation 0 수렴) → prepare.py 4410 samples →
  combine 4설계(gcd 53 + aes 691 + ibex 2040 + jpeg 4410 = 7194행). **의의**: 교차설계 LODO/T1이 3→4
  fold가 되어 Wilcoxon 통계력↑, ibex(자릿수 다른 분포) 단독 의존 완화 — gen-004~007에서 "probe only/강한
  결론 보류"였던 게이트를 통계 유의성으로 격상할 기반. **방법론**: 기존 Sub-A spec/plan(2026-06-09)·
  Fargate flow·prepare.py·combine 파이프라인을 *코드 변경 거의 없이 재사용* — 한 설계 추가가 검증된 절차.
  **운영**: AWS는 실 과금이라 D4 비용 게이트(Operator per-instance 동의) 준수, run-task 후 즉시 cdk
  destroy로 비용 정지(스택 does-not-exist 확인). region 실제값 ap-northeast-2(DEPLOY.md us-east-1은 stale).
  gen-008+는 4설계 dataset 기본값. 한계: jpeg도 한 설계일 뿐 — 더 많은 설계가 LODO 유의성을 더 키움.

- **2026-06-21b** (gen-007 — 새 4단 체인 첫 실전, LODO↔T1 역할 분담 입증) — 게이트 정합(교차설계 T1)
  후 첫 자율 세대. winner cand-002가 median val_mae **1.29**(gen-004~006의 3.5~3.7 대비 역대 최저)로
  뽑혔고 LODO도 통과(`generalizes_better`, 우세 2/3)했으나, 교차설계 T1에서 `indistinguishable`
  (mean_diff +0.36, CI[−0.82,+1.55], p=0.655, dz=0.10) → `rejected_t1`. **(1) 게이트 역할 분담 입증**:
  LODO는 "설계 *수*로 누가 이겼나"(방향성), T1은 "그 격차가 *통계적으로 유의한가*". winner는 방향성은
  좋아도 격차가 noise에 묻혀 차단 — 정확히 T1의 존재 이유. per-design: winner가 aes(1.28 vs 2.68)·
  gcd(2.04 vs 2.52) 우세이나 **ibex(6.93 vs 2.96)서 크게 패배**(평균 격차 +0.69) → LODO는 2설계 우세로
  통과, T1은 ibex 패배 반영해 유의성 부정. **(2) val_mae ≠ 일반화 재확인**: gen-007 winner는 역대 최저
  val_mae인데도 T1 `indistinguishable`, gen-006 winner(val_mae 3.50)는 `distinguishable`이었음 — median이
  낮다고 교차설계 일반화가 좋은 게 아님. **(3) 게이트가 위양성 차단**: 역대 최저 median이 자율 승격됐다면
  baseline이 오염됐을 것 — 새 체인이 정확히 막음. 한계: 저표본(설계 3) + 반복-상관 → 더 강한 결론은
  설계 확보(Sub-A) 후.

- **2026-06-21** (게이트 충돌 해소 — T1을 교차설계 통계 게이트로 재정의, 판정 반전이 측정축 차이를 입증) —
  gen-006이 드러낸 LODO↔T1 모순(stated bar=LODO ≠ enforced bar=LODO AND 혼합-T1)을 선택지 A2로 해소.
  T1의 fold 스킴을 혼합 K-fold → **repeated leave-one-design-out**(D×R fold)으로 교체해 T1이 LODO와
  같은 축(교차설계 일반화)을 통계 검정하게 만듦. **핵심 증거**: gen-006 winner를 새 게이트로 재평가하니
  혼합-T1 `worse`(mean_diff +0.45, dz +2.89) → 교차설계-T1 **`distinguishable`**(mean_diff −0.53,
  CI[−0.86,−0.23], p=0.003) — *같은 winner, 정반대 verdict*. 게이트가 측정축을 바꾸자 판정이 뒤집힘 =
  두 게이트가 진짜 다른 것(robustness↔accuracy)을 측정함을 통계로 입증. 새 체인이었다면 gen-006은
  승격 후보였음 → program.md 힌트 강화 효과가 게이트 정합 후 비로소 승격으로 이어질 수 있음.
  **권력분립 4단 적용**: spec(block: A2 권한 근거·3-tuple naive 누락 → 수정), plan(request_changes:
  sorted-order 테스트·gen-006 재평가 필수화·scheme 정확분기), code(approve) — 각 단계 Codex가 고유 결함
  적발. **방법론**: 코드 한 줄 안 건드리고 지시문만 바꾼 가설(힌트 강화)이 게이트 정의의 숨은 모순을
  노출했고, 그 모순 해소가 다시 "게이트가 옳은 축을 측정해야 한다"는 invariant를 코드화 — Operator 학습
  ↔ 프로젝트 진화의 양방향. 한계: 저표본(설계 3) + 반복-상관 → 강한 결론은 설계 확보(Sub-A) 후.

- **2026-06-20** (gen-006 — 힌트 강화가 LODO 벽을 넘김, 그러나 LODO↔T1 게이트 목표 충돌 표면화) —
  강화된 program.md(승격 기준=LODO salience)로 gen-006 자율 실행. **(1) 가설 지지**: winner
  cand-001(codex/moderate, val_mae 3.50)이 **처음으로 LODO 통과**(우세 2/3, 평균 −0.083,
  `generalizes_better`) — gen-004/005의 0~1/3 후퇴에서 반전. "생성 단계가 일반화 병목"이라는 가설을
  지지하고, *코드 한 줄 없이 지시문만으로* 자율 루프 행동을 바꿀 수 있음을 실증. **(2) 게이트 충돌**:
  그러나 T1(50-fold repeated K-fold, 설계 *혼합*)에서 winner 2.92 vs baseline 2.48 → `worse`(p=0.000,
  dz=2.89) → `rejected_t1`. **LODO(미관측 설계 강건성)와 T1(in-distribution 정확도)이 부분적으로 상반된
  목표를 측정** — winner는 교차설계 강건성을 얻는 대가로 혼합-CV 적합을 희생(robustness↔accuracy
  트레이드오프). 내가 program.md에 "승격 기준=LODO"라 적었으나(Codex 승인) 실제 체인은 `LODO AND T1`이고
  T1은 LODO와 다른 걸 강제 → **stated bar와 enforced bar의 불일치**가 드러남. co-evolution: Operator 학습
  (힌트 강화)이 게이트 정의의 숨은 모순을 표면화. 해소 방향(T1을 LODO-style held-out-design fold로
  재정의 vs LODO+T1 공동요건 유지)은 spec-level 결정 — Operator 판단 대기. **(3) 2차 harness 갭**:
  cand-000이 *산문 머리말+코드*(펜스 없음)를 반환 → `_looks_like_source` 토큰 검사가 코드부 토큰만 보고
  통과 → SyntaxError(inf). gen-004 순수-산문과 다른 변종. `ast.parse` 기반 강화가 후속(token 검사는
  parseable을 보장 못 함).

- **2026-06-20** (gen-005 — harness 수정 검증 + 2세대 연속 일반화 후퇴 패턴) — `_looks_like_source`
  가드를 넣은 harness로 gen-005 자율 실행. **(1) 수정 검증**: 후보 유효율 2/4(gen-004) → **4/4**.
  gen-004서 산문 반환으로 크래시했던 cand-002가 이번엔 distinct 유효 변형(median 4.27, per-seed가
  baseline과 상이 → fallback 아님)을 냄 — 정상 변형 false-reject 0도 동시 확인. **(2) 반복 패턴**:
  winner cand-001(codex/moderate, val_mae 3.70)이 held-out 3개 설계 **전부**서 baseline 후퇴(우세 0/3,
  평균 +0.043) → `rejected_lodo`. gen-004(1/3)·gen-005(0/3) **2세대 연속** median-winner가 교차설계서
  baseline보다 나쁨 — 에이전트 변형이 *val_mae는 낮추나 진짜 일반화는 개선 못 함*. LODO 게이트가
  baseline 오염을 두 번 막아 운영 가치 반복 실증. **(3) 함의**: 같은 baseline·dataset에서 진화가
  교차설계 일반화 개선에 막혀있음 → 다음 지렛대는 후보 재추첨(stochastic)보다 **(a) program.md 힌트
  강화로 일반화 지향 변형 유도, (b) 설계 확보(Sub-A)로 LODO를 probe→유의성 격상** 중 하나. negative
  result(승격 0건)가 "어디서 막혔나"를 가리키는 진단 신호로 기능. **후속 실행**: 지렛대 (a)를 택해
  program.md 힌트를 강화(승격 기준=LODO salience + gen-004/005 사실)했고, 이 *지시문* 변경을 Codex
  검토 게이트에 태우자 첫 판정에서 **block** — 내가 쓴 "val_mae는 부분 holdout" 프레이밍이
  GroupShuffleSplit(설계-분리) 사실과 모순임을 적발(수정→approve). 검토 게이트의 가치가 spec/plan/code를
  넘어 *자율 루프를 좌우하는 instruction-doc*까지 확장됨 — 생성자(나)의 자기검토는 같은 오해를 공유했을 것.

- **2026-06-19** (첫 자율+LODO 게이트 세대 — 비개선 winner를 자동 차단, harness 견고성 갭 노출) —
  루프 환류로 구현한 LODO 게이트를 단 첫 자율 세대 gen-004(3설계 혼합 dataset, `--auto`)에서 실측.
  median winner는 cand-003(codex/conservative, val_mae 3.74)이 선발됐으나, **held-out LODO에서
  baseline보다 후퇴**(winner 우세 1/3, 평균 격차 +0.015) → `verdict=worse` → **`rejected_lodo`로
  자동 차단**(T1·Codex 생략, fail-fast). 세 fold 전부 유효(n_valid=3=n_designs)라 부분실패 차단이
  아니라 *진짜 일반화 후퇴 판정* — gen-002 위양성의 코드화된 방지가 자율 세대에서 처음 발화. baseline
  불변 유지, winner 없음. **(1) negative result = 산출물**: 승격 0건이지만 "median-best가 교차설계
  일반화-best와 다를 수 있고 게이트가 그 간극을 잡는다"가 실증됨 — 접근성/프로세스 novelty 축에 직접
  기여. **(2) 혼합훈련 회복 재현**: baseline·winner 모두 ibex held-out서 naive를 4.3× 격파(2.96 vs
  12.81) — 2026-06-11b 발견이 자율 세대에서도 성립. **(3) 자연 도태 ≠ harness 버그**: cand-001은
  `VotingRegressor`에 sklearn 규약 미충족 추정기를 넣어 fit 크래시(정직한 도태), 그러나 cand-002는
  claude가 "소스만 출력" 계약을 어기고 채팅 산문("✅ …완료")을 반환했는데 `sdk.py:_extract_code`가
  코드펜스 부재 시 산문 전체를 train.py로 기록 → `✅` SyntaxError. **harness 견고성 갭**(도태가 아니라
  버그) — `_extract_code` 가드 보강이 후속 과제. **(4) co-evolution**: 사람이 만든 게이트가 자율 루프를
  *신뢰가능*케 한다는 2026-06-08 재피벗 가설이 첫 자율 세대에서 검증 — Operator는 결과를 보기 전
  게이트를 고정했고(사전 고정 판정), 게이트가 비개선을 차단해 baseline 오염을 막음.

- **2026-06-16** (Codex 검토 게이트가 첫 dogfood에서 spec 결함 적발 — 사람 워크플로의 권력분립) —
  검토·승인을 객관화하는 `codex-review-approval` 스킬을 만들고(Codex MCP `mcp__codex__codex`로 verdict
  위임, 생성자 Claude ≠ 판정자 Codex), 그 첫 대상으로 루프 환류 spec(2026-06-12)을 검토. **block**:
  spec이 재사용한다던 `run_crossdesign_gate`는 일부 fold 실패(inf) 시 *유효 fold만으로* 통과형
  verdict(`generalizes_better`/`mixed`)를 낼 수 있어, spec §7의 "fold 실패→unverifiable→차단" 의도와
  어긋남 — **부분 실패한 LODO가 게이트를 통과**하는 안전 구멍. 함수를 순수 probe로 두고 orchestrator가
  `n_valid < n_designs`를 `rejected_lodo`로 차단하도록 spec 수정 → 재검토 **approve**. (1) **자율 루프의
  권력분립을 사람 워크플로로 확장**: gen-003에서 Codex가 T1을 속인 gaming을 잡았듯, 여기선 Codex가
  *내(생성자)가 자기검토로 못 본 spec-코드 간극*을 잡음 — 통계도 자기리뷰도 못 잡는 층을 독립 엔진이
  덮는다. (2) **co-evolution**: 검토 도구를 만든 그 세션에 그 도구가 산출물을 개선 → 도구가 의도(객관
  검토)를 즉시 실증. (3) **운영**: Codex MCP는 `.mcp.json` 등록 후 *세션 재시작*에 활성(staleness
  invariant). 스킬: [[project-codex-review-approval-skill]], `.claude/skills/codex-review-approval/`.
  **(후속, 같은 날)**: 루프 환류 spec→plan→구현을 끝까지 진행하며 같은 Codex 게이트를 *세 단계 모두*에
  적용 — spec(1건: 부분실패 LODO가 게이트 통과하는 안전 구멍), plan(3건: 단일설계 "LODO 생략" 미명기·
  비교성 경고 리포트 누락·frozen 검사 누락), code diff(1건: program.md 게이트 체인이 LODO 누락) 결함을
  각각 적발→수정→재검토 approve. **객관 게이트를 단계마다 거니 각 단계의 고유 결함이 드러났다**(spec은
  의미 간극, plan은 spec 커버리지, code는 문서-구현 정합). 산출물: gen-004+ 자동 게이트가
  median→**LODO**→T1→Codex 4중 권력분립(부분실패 fold까지 차단), 루프 dataset 3설계 혼합본 교체,
  세대 리포트·program.md에 일반화 노출. 구현 plan: `docs/superpowers/plans/2026-06-16-loop-crossdesign-integration.md`.

- **2026-06-11b** (ibex 3설계 3-fold — 혼합 분포 훈련이 절대 모델 전이를 회복, 단일 정답 축은 없음) —
  B+A 병렬 실행(ibex Fargate 77분·2040 samples·파서 무변경 + 로컬 V4 조합 probe). 결과 셋:
  (1) **V4(V1×V3 조합)는 V1 단독보다 악화**(aes 1.29/gcd 3.89) → 조합 탐색 종료(2-fold 다중비교
  과적합 경고 준수). (2) **혼합 분포 훈련의 효과**: 3-fold(훈련 fold에 2설계 혼합)에서 winner가
  held-out ibex의 naive를 **4.3× 격파**(2.96 vs 12.81) — 전날 "모든 학습 모델이 naive 이하" 결론은
  *단일설계 훈련*의 한계였음이 부분 반증. 설계 다양성 자체가 절대 스케일 모델의 전이를 살린다.
  (3) **V1(델타)의 적용 경계 발견**: ibex는 synth→route 드리프트가 거대(델타 평균 ~12.8ns)해 훈련
  설계의 델타 분포(~1.5ns)와 자릿수가 다름 — **델타도 분포 밖 외삽엔 약함**(V1 6.44, naive보단
  2× 낫지만 winner에 패배). 잔차 학습은 드리프트가 설계 간 안정적일 때의 무기. (4) **held-out별
  최선이 갈림**(aes→V1 / gcd→naive / ibex→winner+혼합훈련) → 교차설계 일반화는 단일 축이 아니라
  설계 특성 조건부 — 다음은 Operator 수동 조합이 아니라 **루프 환류**(에이전트가 trade-off 탐색,
  게이트는 3-fold LODO)가 자연스러운 수순. (5) 운영 마찰 2건 기록: zsh가 `"$VAR:latest"`의 `:l`을
  소문자화 modifier로 해석해 ECR repo명을 변형(`${VAR}:latest`로 회피 — 이전 세션의 `...atest`
  유령 이미지도 같은 원인), ECR repo가 `emptyOnDelete`라 destroy 시 runner 이미지도 소멸(재배포 시
  retag+push 필요, 로컬 docker 캐시 덕에 빌드는 생략). 리포트:
  [probe-3design.md](experiments/multidesign/probe/probe-3design.md).

- **2026-06-11** (정규화 probe — 델타 label이 교차설계 전이를 살리는 지배 축) — 전날 발견(분포 shift가
  모든 학습 모델을 naive 이하로 무력화)에 대한 대응 probe. 변형 3개를 winner train.py 사본으로 만들어
  (V1 델타 label · V2 설계별 통계 표준화 · V3 무차원 비율) gcd+aes LODO 2-fold로 실측, **판정 기준은
  결과 확인 전 사전 고정**(두 설계 모두 naive 미만 = transferable — gen-002 교훈). 결과:
  **V1 `partial`** — held-out aes에서 1.0824로 **naive(1.7198)를 37% 격파, 교차설계에서 naive를 이긴
  첫 모델**(훈련 데이터가 gcd 53행뿐인데도). held-out gcd에선 1.5723로 naive(1.4117) 미달이나
  winner(2.51) 대비 대폭 개선. V2·V3은 `not_transferable`(단 V2는 표준화된 stages가 사본의 per-stage
  feature를 노이즈화하는 교란, V3은 절대 앵커 제거로 naive 표현 불가 구조 — 리뷰가 사전 발견한 해석
  caveat 병기). (1) **label 오프셋 제거(잔차 학습)가 분포 shift 대응의 지배 축** — feature 스케일
  정렬(V2·V3)만으로는 부족. (2) **전이 비대칭**: gcd(53행)→aes는 성공, aes(691행)→gcd는 부분 실패 —
  데이터 양보다 분포 방향이 지배, 제3 설계의 가치 시사. (3) **프로세스**: 사전 고정 판정 + 변형은
  통제변인 1개씩(사본) + 리뷰 caveat을 결과 해석에 선반영 — "싼 probe가 비싼 결정(ibex)을 정보화"
  패턴 2회째. 후속: V1 축 조합·ibex 3-fold 확장은 별도 브리프. 리포트:
  [probe.md](experiments/multidesign/probe/probe.md).

- **2026-06-10** (첫 교차설계 실측 — 분포 shift가 모든 학습 모델을 무력화) — T4-lite Sub-A payoff.
  gcd 53행(slack −1.37~0) + aes 691행(+0.44~+2.93)을 `combine_datasets`로 결합(744행), Sub-B
  `run_crossdesign_gate`(LODO 2-fold)를 실데이터에 첫 가동. winner(gen-001 train.py) vs
  baseline(pre-gen-001 사람, `619e24f~1`). 결과: verdict **`mixed`**(aes held-out에선 winner
  2.74<baseline 3.05, gcd held-out에선 baseline 2.44<winner 2.51). (1) **진짜 발견은 verdict가
  아니라 naive와의 격차**: 두 모델 모두 naive(항등 예측 synth=post_route, 훈련 데이터 미사용)
  1.72/1.41에 크게 패배 — within-design MAE 0.10–0.15가 미관측 설계에서 2.5–3.0으로 **~20× 붕괴**.
  분포가 정반대인 설계 간엔 *어떤* 학습 모델도 전이 안 됨(결정 브리프 시나리오 1, 정직한 negative).
  (2) **원인 가설**: feature가 절대 ns 스케일이라 훈련 범위 밖 설계는 순수 외삽; naive는 훈련
  데이터를 안 써 shift 면역. → 후속 방향은 설계 수 늘리기(ibex 3-fold)보다 ① 양/음 slack이 훈련
  fold에 섞이는 구성 ② feature 정규화(상대 slack 등)가 선행 후보 — **ibex run-task는 이 재평가 후
  결정**(지출 전 싼 검증이 지출의 가치 자체를 바꾼 사례). (3) **H-A의 범위 한정 확인**: 에이전트
  우위(dz=−1.27)는 within-design 증거이며 cross-design으로 자동 연장되지 않음 — held-out *설계*
  게이트가 auto-promote에 편입되기 전엔 일반화 주장 금지. (4) **기계 검증**: 교차설계 게이트가
  합성 fixture 밖 실데이터에서 정상 작동(2 fold valid, tempdir 격리). 리포트:
  [crossdesign.md](experiments/multidesign/crossdesign.md).

- **2026-06-08** (auto-gate 첫 자율 실행 — Codex가 T1이 못 잡는 gaming 차단) — `make loop --auto`로 gen-003을
  **완전 무인** 실행(사람 개입 0). median이 codex 후보(cand-001, median 0.0786)를 선택 → **T1 통계 게이트
  통과**(winner 0.1025 vs baseline 0.1476, mean_diff −0.0452, 95% CI [−0.053,−0.037], p<0.001, **dz=−1.51**,
  verdict `distinguishable`) → 그러나 **Codex 승격 심사관이 차단**(`rejected_codex`). Codex 사유: 후보가
  `for model in models: mae=MAE(y[va], model.predict); if mae<best: best_model=model` 로 **바로 그 검증셋(va)에서
  best_model을 골라** 그 최솟값을 val_mae로 보고 — **post-selection bias / metric gaming**(train.py:232–245, grep
  확증). 이 꼼수는 fold마다 진짜 낮은 MAE를 내 **T1을 구조적으로 속인다**(그래서 distinguishable). (1) **권력분립의
  결정적 실증**: 순수 통계 게이트였다면 gamed 모델을 자동 승격했을 것(dz=−1.51로 "명백 우수"). 의미 게이트(Codex)가
  코드를 읽어 leakage를 차단 — 두 게이트가 *상보적*이고, T1이 못 잡는 걸 Codex가 잡음. (2) **H-B 재정의 작동**:
  사람 없이 신뢰가능한 자율 — 올바른 보수적 거부, train.py·tag 불변, main 무손상. "맹목적 자율 금지(Not)"가 코드로
  실현됨. (3) **자기예언적 co-evolution**: Codex가 이전 리뷰에서 "T1은 fold 독립 가정으로 과신"이라 경고했는데, 바로
  그 약점(val 기반 선택)을 찌르는 후보가 나왔고 Codex 게이트가 막음. (4) **비용 정정**: 루프 LLM 호출은 claude/codex
  **CLI 구독**(추가 과금 0, 구독 사용량만) — metered API 미사용([[project-subscription-only-no-metered-llm]]).
  후속: 검증 게이트가 fold 작업물 126M를 `gen-NNN/t1/`에 남김 → tempdir로 옮기는 소소한 개선 필요.

- **2026-06-08** (재피벗: Operator authority → 비전문가 empowerment) — Operator가 "수동승인(H-B)을 핵심으로 꼽는 현 프레이밍은 과했다 — Karpathy식 자율 진행이 기본이어야 하고, 사람은 방향·큰 흐름만 이해·조종하면 된다. 목표는 비전문가가 전문영역서 의미있는 성과를 내는 것"이라 판단. **novelty 축 이동**: "자율 무인 vs Operator authority"(거버넌스) → **"비전문가 empowerment + 큰 흐름의 이해가능성"**(접근성). INTENT Not의 "자율 무인 머지 절대 금지"를 **"맹목적 자율 금지(객관적 게이트+이해가능성이 조건)"** 로 교체, H-B를 "per-winner 승인 없이 방향·이해만으로 신뢰가능한 자율" 로 재정의. **핵심 연속성**: 직전에 만든 T1 게이트가 버려지지 않고 *격상*됨 — advisory(사람 보조)에서 → *자율 승격을 신뢰가능케 하는 자동 판정자*로. 즉 엄밀 게이트가 있어야 사람을 per-winner 결정에서 뺄 수 있으니, T1이 자율성의 *전제조건*이 된다. status `clarified → exploring` (Learnings #1 예언대로 "되돌아감 자체가 co-evolution 신호" 실현 — 운영 통찰이 의도를 재변형). 후속: TUTORIAL/README/CLAUDE/PRD를 이 축으로 정합, 루프의 자동 승격 구현(operator_gate→auto-gate)은 별도 spec.

- **2026-06-08** (T1 승격 검증 게이트 + H-A 엄밀 재확증) — gen-002 위양성을 계기로, "주장의 신뢰성"을
  고치는 **승격 검증 게이트**(T1)를 brainstorm→spec→plan→subagent TDD(59 tests)→2단계 리뷰
  (approve-with-fixes: Cohen's dz 부동소수 잔차 가드 `1e-9`, 불안정 verdict 리포트 명시)로 구축.
  repeated 5-fold×10(50 fold) paired로 naive·baseline·winner를 비교, Wilcoxon+bootstrap CI+dz를
  Operator에 advisory 제시(자동 거부 없음 — H-B). 기존 `run_candidate`+`score_holdout` 재조합이라
  새 위험 없음. train.py/prepare.py/dataset frozen 무변경. **이는 더 큰 프로그램
  "Trustworthy Automated Research"(로드맵 T1→T3→T4→T2)의 1단계.** (1) **H-A는 약화가 아니라 강화됐다**:
  gen-001 소급 재심 결과 winner(0.148) vs 사람 baseline(0.194) mean_diff −0.0466, 95% CI [−0.057, −0.037]
  (0 미포함), p<0.001, **dz=−1.27(큰 효과)** → verdict `distinguishable`. 단일 seed 점추정이 아닌
  엄밀 paired 통계로도 에이전트 우위가 유지됨 — gen-001 승격은 정당. (2) **게이트가 "도약"과 "노이즈"를
  구분한다**: gen-001(사람→에이전트, 큰 도약)은 robust, gen-002(미세 개선)는 노이즈에 묻힘 — 둘은
  모순이 아니라 *서로 다른 효과크기*. 엄밀 게이트가 이 둘을 분리하는 게 핵심 기여. (3) **co-evolution
  지속**: 위양성(2026-06-07) → 엄밀성 게이트(2026-06-08) → 그 게이트가 H-A를 재확증하며 *이전 caveat을
  뒤집음*. negative result가 방법론을 진화시키고, 진화한 방법론이 첫 주장을 더 단단히 만든 순환.
  (4) **남은 한계**: 단일 설계 n=53 — 일반화는 미검증, held-out *설계*(T4)가 다음 필연.

- **2026-06-07** (gen-002 위양성 → median harness co-evolution) — gen-002 실행에서 Codex 후보가 단일 seed=0 val_mae 0.0992로 winner 선택됐으나, **다중 seed 검증에서 일반화 실패**가 드러남. 53샘플·random split이라 seed별 val_mae가 0.05~0.16으로 출렁여, seed=0이 우연히 그 후보에 유리한 split이었을 뿐. (1) **단일 seed selection이 위양성을 만든다**: 새 5-seed median harness로 재평가하니 단일-seed winner(codex)가 셋 중 **꼴찌**(median 0.0992), baseline(gen-001 winner) 0.0865가 최저 → gen-002 **reject**. "에이전트가 baseline 능가"(H-A)가 *측정 아티팩트*일 수 있음을 실증 — gen-001의 0.11도 같은 의심 하에 재검토 필요. (2) **H-B가 broken winner 승격을 막았다**: 자율 무인이었다면 0.0992를 보고 그냥 승격해 일반화 안 되는 모델이 baseline이 됐을 것. Operator 게이트 + 재검증이 차단 — H-B의 운영 가치가 두 번째로 실증됨. (3) **co-evolution**: 위양성이라는 운영 마찰이 **평가 프로토콜의 진화**(single seed → median harness, [spec](docs/superpowers/specs/2026-06-06-multiseed-median-selection-design.md))를 낳음. brainstorm→spec→plan→subagent TDD(45 tests)→2단계 리뷰(approve-with-fixes: per_seed_vals inf→null RFC8259 가드)로 harness를 Operator-소유 채로 확장(train.py frozen 계약 무변경). 진화한 프로토콜이 다시 gen-002 결론을 뒤집음 = Operator 학습 ↔ 프로젝트 진화의 양방향. (4) **negative result도 산출물**: gen-002는 reject지만, "단일 seed 선택은 노이즈 데이터에서 신뢰 불가"라는 프로세스 발견이 본 프로젝트의 거버넌스 novelty 축에 직접 기여. OD-5(데이터 한계)가 selection 프로토콜로 전파된 사례 — 정밀 임계값은 다설계 확보 후 여전히 미결.

- **2026-06-06** (시스템 빌드 + gen-001 H-A/H-B 실증) — 한 세션에서 피벗 골격 → **작동하는 AutoResearch 시스템 + 실제 1세대 promotion**까지. (1) **검증-우선이 설계를 바꿨다**: 합성 fixture로 "resolved"였던 OD-2/OD-3가 진짜 gcd flow로 *falsify*됨 — 두-시점 critical path가 disjoint(F3)·두-줄 헤더(F1)·QEMU가 CTS 불가(F4). per-path → **endpoint 단위 다설계 pairing**으로 재설계하고 파서를 고침. native x86 Fargate(5회 deploy iter: env.sh·argv·awscli v2·report_checks stdout)로 진짜 post-route 확보 → prepare.py가 **n_samples=53** 생성. 합성으로는 절대 안 나올 마찰들. (2) **H-A 첫 확증**: Claude+Codex headless가 train.py를 자율 변형 → 둘 다 baseline(val_mae 0.177) 능가, Codex winner(VotingRegressor + 도메인 feature engineering) **~0.11**(naive 1.41 대비 13.5×). 단순 sweep 아닌 *구조적 아이디어*(H1b). (3) **H-B 확증**: 루프가 winner를 `awaiting_operator`로 멈추고 **승격은 Operator 승인 후에만** — baseline 불변이 코드 구조로 강제됨. AutoResearch-RL의 "human asleep auto-merge"와 정반대. (4) **AutoResearch가 진짜 마찰을 표면화**: winner 모델이 `FunctionTransformer`를 `__main__` 참조로 pickle해 held-out 재채점이 깨짐 — 합성 테스트로는 안 나오고 *진짜 에이전트가 진짜 코드를 생성*해야 드러나는 종류. holdout 견고화로 수정. (5) **검증 게이트는 사람에게도 적용**: Operator(Claude)가 promote 커밋 시 `&&` 체인이 pytest를 게이트 안 해 broken main을 2커밋 동안 방치 → 즉시 복구. H-B의 "검증" invariant가 *Operator 자신의 워크플로*까지 확장됨(Learnings #3/#5 계열). (6) **co-evolution**: status exploring → **clarified** — 의도가 *빌드+실증*으로 수렴. Operator가 배운 운영 invariant(region 기본값 ap-northeast-2·awscli v2·OpenROAD argv 미지원·report_checks stdout)가 곧 커밋된 substrate가 됨 = Operator 학습 ↔ 프로젝트 진화의 양방향이 구체화. OD-1~6 전부 resolved(OD-5 정밀 임계값만 다설계 후).

- **2026-05-29** (피벗) — 통합 프로그램(L1/L2/L3 3-layer × 5축)이 Operator 1명 6개월에 과도하다는 판단으로 **AutoResearch 기반 EDA surrogate 모델 자동 연구**로 축소 피벗(brainstorming 6문항). Perplexity grounded 조사로 positioning 확인: surrogate ML-for-EDA(CircuitNet 등)도, AutoResearch(karpathy/AutoResearch-RL)도 각각 성숙하나 *AutoResearch 루프로 EDA surrogate를 학습 + Operator-in-loop 감독*의 결합은 부재. 차별 축은 기술 substrate가 아니라 **자율 무인(AutoResearch-RL의 "human asleep") 대비 Operator authority + (연기) reasoning trace**. 의도가 clarified → exploring으로 *되돌아간 것 자체*가 co-evolution 신호 — 의도공학 layer가 "범위 과대"라는 운영 마찰을 흡수해 의도를 재수렴시킴. 기존 3-layer 전량은 archive 브랜치에 보존(무손실), main은 PRD 중심 serverless-autoresearch 정렬 골격으로 재편.

## Learnings (archived — 통합 프로그램 3-layer)

> 아래는 피벗 이전 통합 프로그램에서 누적된 학습. 메타 패턴(검증 invariant·의도공학 dogfooding)은 피벗 후에도 유효하므로 보존한다.

- **2026-05-10** — INTENT.md 첫 작성. 초안에서 (?)로 표시했던 4개 영역 중 H1a / H1b / H1c 정량 임계값이 모두 overview spec §5.4 에 이미 nail down되어 있음을 발견. **의도공학 layer 첫 invariant**: INTENT.md 는 spec 과 *정합* 해야지 *spec 을 다시 정의* 하면 안 된다. spec 권한과 INTENT 권한의 layer 분리가 INTENT.md 단위에서 처음 명시됨.

- **2026-05-10** (agent dogfooding 첫 시도) — 4 위임 agent 정의 commit 직후 `experiment-designer` 호출 시 "Agent type not found" 오류. **운영 invariant**: agent 정의 ↔ 호출 가능성 사이에 *세션 재시작이 필요한 시간 지연*이 존재. 의도공학 layer가 의도(추상) → agent system prompt(구체) → *호출 가능 시점*(시간) 의 3 단계임을 첫 dogfooding이 드러냄.

- **2026-05-10** (정합 작업) — 직전 turn에 "K2 → K1 backlink 비대칭" 이라 advisory를 적었으나 grep 검증 시 K2 4 페이지 모두 K1 backlink 풍부 보유. **추측이 사후 grep 검증을 대체하지 않는다는 invariant 확인** — 정합 작업 전 grep 검증이 default.

- **2026-05-10** (agent dogfooding 첫 성공) — 세션 재시작 후 `experiment-designer`가 정상 호출되어 `g1-first-smoke` plan을 message-only로 산출, Operator가 5/5 Q&A 수용 후 commit `2be69ed`·freeze tag `g1-smoke-pre`로 고정. plan이 INTENT.md `Not` declaration table을 먼저 세우고 spec §5.4를 *복사 인용*만 해 INTENT 권한 vs spec 권한 분리 invariant를 지킴. 추상 의도 → system prompt → plan markdown의 3단 계단이 처음 닫힘. Codex reflection — Operator 2026-05-25 *retain* 결정, spec §5.4 H3 evaluator separation rule의 first complete operational cycle로 보존.

- **2026-05-25** (AI 도구의 grounding 검증) — Perplexity `perplexity_research`(Sonar Deep Research) 호출 결과 **citation 0개의 49.9 KB confabulated 응답** 반환("logical extrapolation" 자백 + "LibreSoC's LibreLane" 사실 오류). 동일 service `perplexity_search`(grounded)는 36개 실 URL 반환. **추측 vs grep 검증 invariant의 AI 도구 환경 확장** — `*research*` 도구의 추측 verbosity는 grounded `*search*` 결과로만 검증. CLAUDE.md Operating Invariant 4번째 항목으로 격상.

- **2026-05-25** (agent dogfooding 5-cycle + invariant cascade) — `experiment-designer` → `code-author`(Makefile `SEED`+`lockfile-verify`) → `eda-code-reviewer` MERGE → `code-author` CDK prefix patch → `eda-code-reviewer` MERGE-WITH-FIXES → spec footnote `2c8b5f7`까지 5-cycle이 Operator merge 외 개입 없이 self-stably 종료. 검증 invariant가 agent 운영 loop 내부에서 반복 발화하며 agent self-output을 다른 agent가 독립 grep 검증하는 meta-layer로 확장. GitHub push가 서버측 HTTP 500으로 실패했으나 `.handoff.md` persistence + atomic local commits로 work product 보존, 다음 세션 retry 성공으로 transient 확인. evaluator separation rule의 second complete operational cycle.
