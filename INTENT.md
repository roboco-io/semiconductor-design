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
