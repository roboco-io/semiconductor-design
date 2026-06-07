# INTENT — semiconductor-design (AutoResearch for EDA Surrogate Models)

> status: exploring  (2026-06-08 재피벗: Operator authority → 비전문가 empowerment + 이해가능성)
> created: 2026-05-10 · pivoted: 2026-05-29 · 시스템 빌드+gen-001 실증: 2026-06-06 · 재피벗: 2026-06-08
> 설계: [`docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md`](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md) · [`PRD.md`](PRD.md)
> 이전 의도(통합 프로그램 3-layer, clarified)는 `archive/integrated-program-3layer` 브랜치에 보존.

## Why

**메타 목적 (피벗 후에도 유지)**: (1) 의도공학(intent engineering) 패러다임 우수성의 사례 연구, (2) Operator 학습 ↔ 프로젝트 진화의 co-evolution.

**헤드라인 목표 (2026-06-08 재피벗)**: **비전문가가 전문영역(EDA)에서 자율 에이전트를 *방향만 잡아* 의미있는 성과를 내는 것.** 자율 진행이 기본 동력이고, 사람은 *권한자(approver)가 아니라 방향타이자 학습자*다.

**문제**:
- EDA surrogate 모델(합성 직후 feature → 최종 PPA/routability 예측)은 *성숙한* 분야다 — CircuitNet 2.0(20K+ 샘플, routability·IR-drop·timing), RouteNet(조기 DRV 예측), Net2(post-placement wirelength), MasterRTL/SNS(pre-synthesis PPA), "Circuit as Set of Points"(NeurIPS 2023). 그러나 모델 구조·하이퍼파라미터·feature 설계의 *탐색 루프는 여전히 사람이 수작업*한다. 이 루프 자체는 기계적이다.
- karpathy [AutoResearch](https://github.com/karpathy/autoresearch)는 "research를 search로 환원"해 이 루프를 에이전트에 위임했으나 대상은 *LLM 학습*이고, **EDA surrogate 학습에 적용된 사례 없음**.
- AutoResearch와 그 형식화 [AutoResearch-RL](https://arxiv.org/abs/2603.07300)(PPO 메타정책)의 명시적 전제는 *no human in the loop* — "human might be asleep, you are autonomous". 우리도 **자율 진행을 기본으로 채택**하되, 차별점은 *전문가의 감독*이 아니라 **비전문가가 큰 흐름을 이해·조종(comprehensibility·steerability)** 하면서도 자율 루프가 의미있는 전문영역 성과를 내게 하는 것 — 이 사례는 부재.

**가설**:
- **H-A** — AutoResearch의 population-based evolution 루프([serverless-autoresearch](https://github.com/roboco-io/serverless-autoresearch) HUGI 패턴)를 EDA surrogate 모델 학습에 적용하면, 사람-수작업 탐색보다 더 나은 surrogate(낮은 val 지표)를 적은 노력으로 얻는다. (gen-001서 엄밀 paired 통계로 확증 — Learnings 2026-06-08.)
- **H-B (재정의)** — 비전문가 Operator가 **per-winner 승인 없이** 방향(`program.md`)·큰 흐름만으로 자율 루프를 *조종·이해*할 수 있고, 그 산출이 의미있는 전문영역 성과다. 신뢰가능한 자율을 가능케 하는 것은 **객관적 자동 게이트**(median selection + T1 검증)와 **튜토리얼식 이해가능성**이다. (자율이 기본 동력, 사람은 전략적 방향타이자 학습자.)

**확인 방법**:
- 기존 EDA flow 1회로 생성한 고정 데이터셋 위에서, 루프가 만든 surrogate winner의 val 지표를 사람-수작업 baseline과 **엄밀 통계(T1 게이트)** 로 비교 (유의하게 낮으면 H-A 지지).
- 자율 자동 승격 구성이 *맹목적*이지 않음을 보장: 비전문가가 큰 흐름을 따라 의미있는 방향 결정을 내릴 수 있었는지(이해가능성)·산출이 전문영역서 유효했는지 세대 로그·리포트로 확인.
- (?) 정확한 비교 baseline·지표 임계값은 데이터셋 확정 후.

## What

**핵심 기능**:
- [ ] **데이터셋 자가생성**(`prepare.py`): EDA flow 1회 → feature(합성 직후) + label(최종 PPA/routability) 쌍. CircuitNet 류 태스크 참조. `DATASET.flow_lockfile_sha`로 재현성 앵커.
- [ ] **자율 진화 루프**: 세대당 N후보 변형(`train.py`) → 병렬 Spot 학습 → **객관적 자동 게이트(median selection + T1 검증)로 자동 승격** → git tag(`gen-NNN-best`). per-winner 사람 승인 없음.
- [ ] **자동 품질 게이트(T1)**: 자율 승격을 신뢰가능하게 만드는 통계적 자동 판정(naive·baseline·winner paired). *맹목적 자율* 방지의 핵심 — `distinguishable`만 승격.
- [ ] **방향·이해 인터페이스**: Operator는 `program.md`로 *방향*을 잡고, **튜토리얼식 리포트로 큰 흐름을 이해**한다. (개입은 방향 수준, per-winner 아님.)
- [ ] **(연기) reasoning trace 증거 평면**: 후보별 hypothesis/observed effect 누적 — 이해가능성을 강화하는 2차 세대.

**사용자 흐름**:
1. Operator가 `program.md`(방향·지시문)·`config.yaml`(예산·세대수) 설정.
2. 에이전트가 `train.py` 변형 후보 N개 생성·병렬 학습.
3. 루프가 자동 게이트(median + T1)로 winner를 **자동 승격**하고 튜토리얼식 리포트를 남긴다.
4. Operator는 *큰 흐름*을 이해하고 다음 *방향*을 조정한다(per-winner 승인 아님).

**엣지 케이스**:
- Spot 회수 시 job 재시도 (CANDIDATE 1:N JOB).
- 후보가 데이터 누수/과적합으로 val 지표만 좋은 경우 → **T1 자동 게이트가 `indistinguishable`/`worse`로 차단**(사람 거절 대신 통계 게이트).
- (?) surrogate 지표가 복수일 때(slack vs area vs routability) 단일화 방법.
- (?) 방향성 개입과 완전 자율의 경계 — 어느 결정이 "방향"이고 어느 게 "per-winner"인지.

## Not

**절대 금지**:
- **맹목적 자율** — 사람이 큰 흐름을 이해할 수 없는 불투명 진행. 자율 자동 승격은 허용하되, *객관적 게이트(median + T1) 없이* 또는 *튜토리얼식 이해가능성 없이* 진행하는 것은 금지. (2026-06-08 재피벗: 기존 "자율 무인 머지 절대 금지"를 대체 — 무인 머지는 허용, 단 신뢰가능 게이트 + 이해가능성이 조건.)
- 상용 EDA 도구. 오픈소스만 (OpenROAD/Yosys 등).
- functional correctness를 surrogate 예측으로 주장 (surrogate는 근사 예측).
- `prepare.py`(데이터·평가 프로토콜) 변경을 에이전트에 허용 (frozen environment — 공정 비교 보장).

**기술 제약**:
- Python 3.12, uv. ruff 100 char, target-version py312.
- 에이전트는 `train.py` 단일 파일만 변형, 신규 의존성 금지, 고정 학습 예산 (AutoResearch 제약 계승).
- Direct commit to `main` (현재 워크플로).

**범위 밖**:
- 전체 RTL→GDSII 공정 운영 (`archive/integrated-program-3layer`로 분리).
- Parameter sweep 단독 (ORFS-agent 영역) — 본 프로젝트는 surrogate *모델 학습*의 자동 연구.
- 모바일·웹 UI, 다중 사용자.
- (1차) process novelty 증거 평면 — 2차 연기.

**품질 기준**:
- surrogate winner val 지표 < 사람-수작업 baseline, **T1 게이트 verdict `distinguishable`** (H-A 지지 조건).
- 자율 자동 승격은 객관적 게이트(median + T1)를 통과한 winner만 (맹목적 자율 방지).
- **이해가능성**: 비전문가가 각 세대의 큰 흐름·방향을 튜토리얼식 산출물로 따라갈 수 있어야 함.
- 세대 간 결과 재현 (동일 데이터셋·lockfile_sha).
- (연기) reasoning trace 복원 가능.

## Learnings

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
