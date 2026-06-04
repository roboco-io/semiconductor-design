# INTENT — semiconductor-design (AutoResearch for EDA Surrogate Models)

> status: exploring
> created: 2026-05-10 · pivoted: 2026-05-29
> 설계: [`docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md`](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md) · [`PRD.md`](PRD.md)
> 이전 의도(통합 프로그램 3-layer, clarified)는 `archive/integrated-program-3layer` 브랜치에 보존.

## Why

**메타 목적 (피벗 후에도 유지)**: (1) 의도공학(intent engineering) 패러다임 우수성의 사례 연구, (2) Operator 학습 ↔ 프로젝트 진화의 co-evolution.

**문제**:
- EDA surrogate 모델(합성 직후 feature → 최종 PPA/routability 예측)은 *성숙한* 분야다 — CircuitNet 2.0(20K+ 샘플, routability·IR-drop·timing), RouteNet(조기 DRV 예측), Net2(post-placement wirelength), MasterRTL/SNS(pre-synthesis PPA), "Circuit as Set of Points"(NeurIPS 2023). 그러나 모델 구조·하이퍼파라미터·feature 설계의 *탐색 루프는 여전히 사람이 수작업*한다. 이 루프 자체는 기계적이다.
- karpathy [AutoResearch](https://github.com/karpathy/autoresearch)는 "research를 search로 환원"해 이 루프를 에이전트에 위임했으나 대상은 *LLM 학습*이고, **EDA surrogate 학습에 적용된 사례 없음**.
- AutoResearch와 그 형식화 [AutoResearch-RL](https://arxiv.org/abs/2603.07300)(PPO 메타정책)의 명시적 전제는 *no human in the loop* — "human might be asleep, you are autonomous". 비전문가 Operator가 다중 에이전트를 *감독*하며 EDA surrogate 연구를 수행할 수 있는지, 그 감독이 자율 무인보다 재현성·신뢰성에서 나은지에 대한 사례는 부재.

**가설**:
- AutoResearch의 population-based evolution 루프([serverless-autoresearch](https://github.com/roboco-io/serverless-autoresearch) HUGI 패턴)를 EDA surrogate 모델 학습에 적용하면, 사람-수작업 탐색보다 더 나은 surrogate(낮은 val 지표)를 적은 노력으로 얻는다.
- 자율 무인(AutoResearch-RL) 대신 **Operator-in-loop**(winner 선택·머지는 항상 사람)를 유지해도 성능을 잃지 않으며, reasoning trace 누적(2차 연기)으로 재현성·신뢰성에서 차별화된다.

**확인 방법**:
- 기존 EDA flow 1회로 생성한 고정 데이터셋 위에서, 루프가 만든 surrogate winner의 val 지표를 사람-수작업 baseline과 비교 (낮으면 가설 지지).
- Operator-in-loop 구성이 자율 무인 대비 성능 손실 없이 winner를 선택하는지 세대 로그로 확인.
- (?) 정확한 비교 baseline·지표 임계값은 데이터셋 확정 후.

## What

**핵심 기능**:
- [ ] **데이터셋 자가생성**(`prepare.py`): EDA flow 1회 → feature(합성 직후) + label(최종 PPA/routability) 쌍. CircuitNet 류 태스크 참조. `DATASET.flow_lockfile_sha`로 재현성 앵커.
- [ ] **AutoResearch 진화 루프**: 세대당 N후보 변형(`train.py`) → 병렬 Spot 학습 → 단일 val 지표 selection → Operator 승인 후 git tag(`gen-NNN-best`).
- [ ] **Operator 감독 인터페이스**: winner 선택·머지는 항상 사람.
- [ ] **(연기) reasoning trace 증거 평면**: 후보별 hypothesis/observed effect 누적 — 2차 세대.

**사용자 흐름**:
1. Operator가 `program.md`(지시문)·`config.yaml`(예산·세대수) 설정.
2. 에이전트가 `train.py` 변형 후보 N개 생성·병렬 학습.
3. 루프가 val 지표로 winner 후보 제시.
4. Operator가 검토·승인·git tag commit → 다음 세대 baseline.

**엣지 케이스**:
- Spot 회수 시 job 재시도 (CANDIDATE 1:N JOB).
- 후보가 데이터 누수/과적합으로 val 지표만 좋은 경우 → Operator 거절 (+연기된 trace).
- (?) surrogate 지표가 복수일 때(slack vs area vs routability) 단일화 방법.

## Not

**절대 금지**:
- 자율 무인 루프로 winner 무검토 머지 (AutoResearch-RL의 *no-human* 전제를 따르지 않음 — Operator authority 유지).
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
- surrogate winner val 지표 < 사람-수작업 baseline (가설 지지 조건, (?) 임계값 데이터 확정 후).
- 세대 간 결과 재현 (동일 데이터셋·lockfile_sha).
- (연기) reasoning trace 복원 가능.

## Learnings

- **2026-05-29** (피벗) — 통합 프로그램(L1/L2/L3 3-layer × 5축)이 Operator 1명 6개월에 과도하다는 판단으로 **AutoResearch 기반 EDA surrogate 모델 자동 연구**로 축소 피벗(brainstorming 6문항). Perplexity grounded 조사로 positioning 확인: surrogate ML-for-EDA(CircuitNet 등)도, AutoResearch(karpathy/AutoResearch-RL)도 각각 성숙하나 *AutoResearch 루프로 EDA surrogate를 학습 + Operator-in-loop 감독*의 결합은 부재. 차별 축은 기술 substrate가 아니라 **자율 무인(AutoResearch-RL의 "human asleep") 대비 Operator authority + (연기) reasoning trace**. 의도가 clarified → exploring으로 *되돌아간 것 자체*가 co-evolution 신호 — 의도공학 layer가 "범위 과대"라는 운영 마찰을 흡수해 의도를 재수렴시킴. 기존 3-layer 전량은 archive 브랜치에 보존(무손실), main은 PRD 중심 serverless-autoresearch 정렬 골격으로 재편.

## Learnings (archived — 통합 프로그램 3-layer)

> 아래는 피벗 이전 통합 프로그램에서 누적된 학습. 메타 패턴(검증 invariant·의도공학 dogfooding)은 피벗 후에도 유효하므로 보존한다.

- **2026-05-10** — INTENT.md 첫 작성. 초안에서 (?)로 표시했던 4개 영역 중 H1a / H1b / H1c 정량 임계값이 모두 overview spec §5.4 에 이미 nail down되어 있음을 발견. **의도공학 layer 첫 invariant**: INTENT.md 는 spec 과 *정합* 해야지 *spec 을 다시 정의* 하면 안 된다. spec 권한과 INTENT 권한의 layer 분리가 INTENT.md 단위에서 처음 명시됨.

- **2026-05-10** (agent dogfooding 첫 시도) — 4 위임 agent 정의 commit 직후 `experiment-designer` 호출 시 "Agent type not found" 오류. **운영 invariant**: agent 정의 ↔ 호출 가능성 사이에 *세션 재시작이 필요한 시간 지연*이 존재. 의도공학 layer가 의도(추상) → agent system prompt(구체) → *호출 가능 시점*(시간) 의 3 단계임을 첫 dogfooding이 드러냄.

- **2026-05-10** (정합 작업) — 직전 turn에 "K2 → K1 backlink 비대칭" 이라 advisory를 적었으나 grep 검증 시 K2 4 페이지 모두 K1 backlink 풍부 보유. **추측이 사후 grep 검증을 대체하지 않는다는 invariant 확인** — 정합 작업 전 grep 검증이 default.

- **2026-05-10** (agent dogfooding 첫 성공) — 세션 재시작 후 `experiment-designer`가 정상 호출되어 `g1-first-smoke` plan을 message-only로 산출, Operator가 5/5 Q&A 수용 후 commit `2be69ed`·freeze tag `g1-smoke-pre`로 고정. plan이 INTENT.md `Not` declaration table을 먼저 세우고 spec §5.4를 *복사 인용*만 해 INTENT 권한 vs spec 권한 분리 invariant를 지킴. 추상 의도 → system prompt → plan markdown의 3단 계단이 처음 닫힘. Codex reflection — Operator 2026-05-25 *retain* 결정, spec §5.4 H3 evaluator separation rule의 first complete operational cycle로 보존.

- **2026-05-25** (AI 도구의 grounding 검증) — Perplexity `perplexity_research`(Sonar Deep Research) 호출 결과 **citation 0개의 49.9 KB confabulated 응답** 반환("logical extrapolation" 자백 + "LibreSoC's LibreLane" 사실 오류). 동일 service `perplexity_search`(grounded)는 36개 실 URL 반환. **추측 vs grep 검증 invariant의 AI 도구 환경 확장** — `*research*` 도구의 추측 verbosity는 grounded `*search*` 결과로만 검증. CLAUDE.md Operating Invariant 4번째 항목으로 격상.

- **2026-05-25** (agent dogfooding 5-cycle + invariant cascade) — `experiment-designer` → `code-author`(Makefile `SEED`+`lockfile-verify`) → `eda-code-reviewer` MERGE → `code-author` CDK prefix patch → `eda-code-reviewer` MERGE-WITH-FIXES → spec footnote `2c8b5f7`까지 5-cycle이 Operator merge 외 개입 없이 self-stably 종료. 검증 invariant가 agent 운영 loop 내부에서 반복 발화하며 agent self-output을 다른 agent가 독립 grep 검증하는 meta-layer로 확장. GitHub push가 서버측 HTTP 500으로 실패했으나 `.handoff.md` persistence + atomic local commits로 work product 보존, 다음 세션 retry 성공으로 transient 확인. evaluator separation rule의 second complete operational cycle.
