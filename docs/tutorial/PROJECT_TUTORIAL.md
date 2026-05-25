# 프로젝트 튜토리얼 — 일반 개발자를 위한 30분 입문

> **대상**: 칩 설계 비전문가, 일반 소프트웨어 개발자 (Python·Git·AWS 기본기는 있음).
> **목표**: 이 프로젝트가 *무엇을 하는지*, *왜 흥미로운지*, *어떻게 구성됐는지*를 30분 안에 파악.
> **이미 알고 있다고 가정**: Git, Python, AWS(S3/Lambda 정도), CI/CD, Docker.
> **모른다고 가정**: RTL, synthesis, place-and-route, DRC/LVS/STA, PDK, sign-off.

본 문서는 6 chapter 구성. 각 chapter는 5분 내외. 다 읽으면 — 이 repo를 git clone했을 때 디렉토리 구조가 *왜* 그런지, `make run`이 어떤 일을 일으키는지, 본 프로젝트가 학술적으로 무엇을 주장하는지 이해할 수 있다.

상세 deep dive가 필요하면 각 chapter 끝의 *"더 깊이"* 링크 참조. 프로젝트의 *역사*(어떻게 진화했나)는 [`docs/vibe-coding-tutorial/`](../vibe-coding-tutorial/) 참조 — 본 문서와 보완 관계.

---

## Chapter 1 — 왜 이 프로젝트가 흥미로운가 (5분)

### 문제

칩 설계는 진입 장벽이 *극단적으로* 높은 분야다. 비교 표:

| 영역 | 진입 비용 |
|---|---|
| 웹 개발 시작 | 노트북 1대 + npm install |
| 머신러닝 시작 | Colab + Hugging Face |
| **칩 설계 시작 (상용)** | 수억~수십억 원 EDA 라이선스 (Synopsys, Cadence, Mentor) + 전문 인력 + 파운드리 계약 |
| **칩 설계 시작 (오픈소스)** | 무료지만 도구가 흩어져 있음 + 학습 자료 부족 |

상용은 비싸고, 오픈소스는 분산돼 있다. 그래서 *AI 시대에 칩 설계를 민주화할 수 있는가?* 가 본 프로젝트의 출발점.

### 본 프로젝트가 채택한 답

**Vibe-coding + AutoResearch + 오픈소스 EDA**. 풀면:

- **오픈소스 EDA**: 상용 도구 없이 LibreLane + OpenROAD + Yosys + sky130A로 칩 한 번 설계까지.
- **AI Agent**: Claude/Codex가 RTL 작성·합성 결과 해석·설계 결정을 *제안*.
- **Operator**: 사람(비전문가) 1명이 agent들의 *제안*을 검토·머지·운영.

> **소프트웨어 비유**: GitHub Copilot이 코드를 *제안*하고 개발자가 *수락/거절*하는 구조 — 그걸 칩 설계로 가져온 것. 단, 단일 자동완성이 아니라 **여러 위임 agent가 분업**(설계 / 실행 / 코드 / 리뷰).

### 메타 목적 두 가지

본 프로젝트가 단순한 "오픈소스 칩 설계 시도"가 아닌 이유 — `INTENT.md`에 명시된 **메타 목적**:

1. **의도공학(intent engineering) 패러다임 우수성 증명** — INTENT.md / spec / wiki / 결정의 *Why* 추적을 통해 LLM 시대의 *문서 = 의도 = 운영* 일치 모델을 사례 연구.
2. **Operator·프로젝트 co-evolution** — 비전문가 Operator가 학습하면서 프로젝트가 진화하고, 진화한 프로젝트가 Operator의 학습을 변형시키는 양방향 순환. *최종 칩보다 이 순환 자체가 publishing 축*.

> **소프트웨어 비유**: DevOps에서 "도구 + 문화"가 같이 진화하듯, "Operator + 프로젝트"가 같이 진화. 단, 여기서는 *측정 가능한 가설*로 만든다 (Chapter 6 참조).

### ✅ Chapter 1 후 알게 되는 것

- 본 프로젝트가 "오픈소스 EDA + Agent 분업 + Operator 감독" 모델로 칩 설계 진입 장벽을 깬다는 것
- 단순 도구 실험이 아니라 *의도공학 패러다임*과 *Operator·프로젝트 co-evolution* 사례 연구라는 메타 목적

**더 깊이**: [`INTENT.md`](../../INTENT.md) (특히 §Why, §고객의 말 anchor).

---

## Chapter 2 — 칩 설계 10분 입문 (소프트웨어 비유 사전) (5분)

칩 설계 용어를 *소프트웨어 개발자가 이미 아는 개념*으로 1:1 매핑.

### 핵심 비유 사전

| 칩 설계 용어 | 소프트웨어 비유 | 본 프로젝트 사용 도구 |
|---|---|---|
| **RTL** (Register-Transfer Level) | 고수준 소스 코드 (`.v`/`.sv` = `.py`/`.go`) | Chisel(Chipyard), Verilog |
| **Synthesis** | 컴파일 (소스 → 게이트 IR) | **Yosys** (`yosys-0.64`) |
| **Place-and-Route (PnR)** | 링커 + 메모리 레이아웃 (게이트 → 칩 평면 좌표) | **OpenROAD** (LibreLane이 wrapper) |
| **PDK** (Process Design Kit) | 타겟 아키텍처 (x86 vs ARM) | **sky130A** (SkyWater 130nm), gf180mcuD 옵션 |
| **`.lib`/`.lef`/`.def`/`.sdc`** | PDK 메타데이터 + 빌드 산출물 파일들 | (위 도구들이 읽고 쓰는 표준 포맷) |
| **DRC** (Design Rule Check) | Lint (규칙 위반 검출) | `magic`, `klayout` |
| **LVS** (Layout vs Schematic) | 통합 테스트 (논리/물리 일치) | `netgen` |
| **STA** (Static Timing Analysis) | 정적 성능 분석 (CPU profile) | **OpenSTA** |
| **Sign-off clean** | CI green (모든 check 통과) | DRC=0 + LVS pass + STA slack ≥ 0 |
| **Tape-out** | 프로덕션 배포 (파운드리에 마스크 전송) | *(본 프로젝트 범위 밖)* |

### `make run` 한 줄로 보면

```
RTL (.v)  →  synthesis (Yosys)  →  PnR (OpenROAD)  →  sign-off check (DRC/LVS/STA)
   ↑                                                              ↓
spec.yaml                                              synth.rpt + sta.rpt + drc.rpt
```

> **소프트웨어 비유**: `npm run build` 와 비슷. spec.yaml은 `package.json`, 산출물 `*.rpt`는 빌드 로그. *clean run* = 빌드 에러 0 + lint 0 + perf 회귀 0.

### 본 프로젝트가 다루는 디자인 (3개)

| 디자인 | 비유 | 복잡도 |
|---|---|---|
| **gcd** | "Hello World" 수준 회로 (greatest common divisor) | smoke test |
| **ibex** | RISC-V CPU 코어 (Lowrisc 프로젝트) | 중간 |
| **aes** | AES 암호 회로 | 큼 |

`gcd → ibex → aes` 순서로 *progressive*하게 실험 (작은 것부터 통과시키고, 점점 큰 것).

### ✅ Chapter 2 후 알게 되는 것

- "Synthesis = 컴파일", "DRC = Lint", "STA = 프로파일러" 비유
- `make run`이 일으키는 5 stage(rtl-build → synth → pnr → signoff → metrics)의 의미
- 본 프로젝트가 다루는 3 디자인(gcd/ibex/aes)의 progressive 구조

**더 깊이**: [`docs/glossary.md`](../glossary.md), [`wiki/eda-flow-report-reading.md`](../../wiki/eda-flow-report-reading.md).

---

## Chapter 3 — 왜 오픈소스 EDA + AI Agent인가 (5분)

### 기존 접근 — ORFS-agent (2025)

ORFS-agent는 본 프로젝트와 가장 가까운 선행 연구. 그들이 한 일:
- **Parameter knob tuning**: PnR 도구의 수십 개 파라미터(예: `place_density`, `core_util`)를 LLM이 *최적화*. baseline 대비 ~13% slack 개선, -40% TNS.

이건 *parameter sweep* 영역이다. 즉, 정해진 조절 손잡이만 돌리는 행위.

### 본 프로젝트의 차별화 축 — *Structural Patch*

본 프로젝트는 그 한 단계 위를 노린다. **agent가 새로운 RTL 변환 / 새 제약 패턴 / 새 synthesis step**을 *제안*. 즉 "도구의 손잡이를 돌리는 것"이 아니라 "도구로 해본 적 없는 조립법을 시도하는 것".

> **소프트웨어 비유**: GitHub Copilot이 함수 시그니처 안에서 함수 본문을 *제안*하는 게 ORFS-agent라면, 본 프로젝트는 *새 함수 자체 + 모듈 구조 변경*을 제안하는 것. 전자는 hyperparameter tuning, 후자는 architectural patch.

### 그래서 어떻게 측정하는가 — H1b 가설

`spec §5.4` 인용:

> **H1b Non-knob structural patch**: 부록 C 제외 transform이 sign-off clean × seed×3 재현, **최소 3건**.

번역:
- "**부록 C 제외 transform**" = upstream tool 공식 문서에 없는 변형 (= structural)
- "**sign-off clean**" = DRC/LVS/STA 모두 통과
- "**seed×3 재현**" = 3개 다른 random seed에서 모두 통과 (반복 가능)
- "**최소 3건**" = 본 프로젝트의 핵심 성공 기준

> **소프트웨어 비유**: "GPT-4가 *완전히 새로운 알고리즘*을 *3개 이상* 작성했고, *3 random seed*에서 모두 *unit test 통과*했다"는 주장에 해당.

### Vibe-coding이란 무엇인가

"vibe-coding"은 본 프로젝트의 *작업 스타일*. 핵심 특성:

- **명령형이 아닌 의도 전달**: Operator가 "이렇게 짜라"가 아니라 "이런 결과를 원한다"를 agent에 전달
- **반복적 검토·머지**: agent 제안 → Operator 검토 → 머지 또는 거절. 거절도 자산(reasoning trace 누적)
- **문서 = 의도 = 운영의 일치**: INTENT.md / spec / CLAUDE.md / agent system prompt가 *서로 정합*. 한 곳을 바꾸면 다른 곳도 따라옴

> **소프트웨어 비유**: TDD에서 "테스트가 spec"인 것처럼, vibe-coding에서 "INTENT.md가 spec". 단, 인간이 직접 코드를 쓰지 않고 agent가 쓴다.

### ✅ Chapter 3 후 알게 되는 것

- ORFS-agent와의 차별화 — parameter sweep vs structural patch
- 본 프로젝트의 핵심 성공 기준 = H1b: 새 구조 3건 × seed×3 재현 × sign-off clean
- "vibe-coding"의 의미 (의도 전달 + 검토 머지 + 문서 정합)

**더 깊이**: [`wiki/raw/papers/k1-beta-agentic-eda.md`](../../wiki/raw/papers/k1-beta-agentic-eda.md), [`INTENT.md`](../../INTENT.md) §What.

---

## Chapter 4 — 프로젝트 구조 한 번에 (5분)

세 가지를 같이 보면 본 프로젝트 전체 구조가 보인다: **3-layer 아키텍처 + 4 위임 agent + wiki-first 라우팅**.

### (A) 3-Layer 아키텍처

| Layer | 한 줄 정의 | 소프트웨어 비유 |
|---|---|---|
| **L1 Process** | SHA-pinned 오픈소스 EDA 스택을 AWS Fargate Spot에서 재현 가능하게 실행 | "CI/CD 인프라" — `docker-compose up` + GitHub Actions runner |
| **L2 Substrate** | L1 산출물·findings·skills를 typed memory로 축적, agent recall API 제공 | "지식 그래프 + 메모리 DB" — Notion DB + vector store |
| **L3 Content** | Open-Ideation agent가 *구조적 patch* 제안 → MLPerf로 평가 | "실험 코드 + 평가 노트북" — Jupyter + W&B |

**관계**: L1 (인프라) ← L2 (메모리·도구) ← L3 (실험 자체). 변경 영향은 *bottom-up only* — L3의 candidate가 L1의 lockfile을 바꿀 수 없음. 이게 **freeze-before-experiment** 원칙.

### (B) 4 위임 Agent

본 프로젝트는 *single-operator multi-agent* 모델. Operator(사람) 1명 + agent 4개:

| Agent | 채널 | 무엇을 하는가 | 비유 |
|---|---|---|---|
| `experiment-designer` | Researcher | 실험 plan markdown 작성 (어떤 candidate, seed, KG 매핑) | "PM이 PRD를 쓰는 것" |
| `experiment-runner` | Researcher | 승인된 plan 실행 (`make run` 호출, 결과 정리) | "QA가 E2E test 돌리는 것" |
| `code-author` | Developer | 코드 작성·수정 (Python/Makefile/CDK) | "주니어 개발자가 patch를 쓰는 것" |
| `eda-code-reviewer` | Developer | 1차 EDA 검사 + `pr-review-toolkit` 오케스트레이션 | "code review 봇 + 시니어 리뷰" |

**머지는 항상 Operator**. agent는 *제안*만, 결정은 사람. 4 agent 모두 INTENT.md "Not" 정합 검사를 system prompt 공통 substrate로 가짐.

### (C) Wiki-First Context Routing

본 프로젝트는 **wiki-first hybrid** 컨텍스트 관리를 채택. 핵심:

- **`wiki/index.md` + 컴파일 페이지** = default routing
- 답변 작성 시 `[[wiki/페이지]]` 인용 강제
- 근거: Karpathy LLM Wiki 72-run 벤치 — 토큰 −53.6%, 시간 −39.3%, 품질 +6% (vs graphify-only)
- graphify는 **보조 도구** — cross-component path 탐색용

> **소프트웨어 비유**: vector DB 검색(graphify)보다 *컴파일된 위키 페이지 인용*(wiki-first)이 토큰·시간 효율적. RAG의 *전처리된 인덱스*가 *원본 임베딩*보다 빠른 것과 같음.

### 디렉토리 한 줄 요약

```
semiconductor-design/
├── INTENT.md                          # 의도 single source of truth (Why/What/Not/Learnings)
├── CLAUDE.md                          # 운영 규칙 + 아키텍처 요약
├── docs/
│   ├── superpowers/specs/             # ★ overview spec + L1/L2/L3 파생 spec (authoritative)
│   ├── superpowers/plans/             # 실험 plan (G1 first smoke 등)
│   ├── vibe-coding-tutorial/          # 프로젝트 *역사* 튜토리얼
│   ├── tutorial/                      # 본 문서 (프로젝트 *구조* 튜토리얼)
│   ├── learning/                      # Phase 0 학습 커리큘럼
│   └── glossary.md                    # 용어집
├── wiki/                              # ★ 컴파일된 default context routing
│   ├── index.md                       # entry point
│   ├── raw/                           # 불변 원본 (K1 52 + K2 61 sources)
│   └── *.md                           # 컴파일 페이지
├── src/semi_design_runner/            # L1 Python 구현체 (CLI, schemas, AWS wrappers)
├── scripts/graph_integrity_check.py   # L2.lint.check 구현체
├── specs/gcd-orfs.yaml                # 샘플 실험 spec (L1.run input)
├── lockfile.yaml                      # SHA-pinned 도구 버전 (재현성 substrate)
├── Makefile                           # make run / make test / make graph-lint
└── .claude/agents/                    # 4 위임 agent 정의
```

### ✅ Chapter 4 후 알게 되는 것

- L1/L2/L3 = 인프라/메모리/실험 3 layer + bottom-up cascading 규칙
- 4 agent = PM(designer) + QA(runner) + Junior dev(author) + Reviewer(eda-reviewer)
- wiki-first = vector DB 검색보다 *컴파일된 위키 인용*이 효율적

**더 깊이**: 이전 plan 파일 [`~/.claude/plans/intent-md-l1-l2-l3-sorted-wozniak.md`](../../../../.claude/plans/intent-md-l1-l2-l3-sorted-wozniak.md), [`.claude/agents/README.md`](../../.claude/agents/README.md).

---

## Chapter 5 — `make run` 한 줄이 일으키는 일 (5분)

가장 구체적 부분. Operator가 터미널에서 한 줄을 친다:

```bash
make run DESIGN=gcd STACK=orfs SEED=42 \
  BUCKET=$S3_BUCKET STATE_MACHINE_ARN=$SFN_ARN
```

이 한 줄이 일으키는 일을 단계별로 추적.

### Step 1 — Makefile substitution (~1초)

`Makefile`의 `run` target이:
- `RUN_ID` 생성 (예: `gcd-orfs-1716636300-s42` — ULID)
- `lockfile.yaml`을 읽어 `l1_lockfile_sha` 계산
- `specs/gcd-orfs.yaml` 템플릿에 `run_id` + `l1_lockfile_sha` 채워서 `/tmp/spec-*.yaml` 생성

> **비유**: Helm chart values 치환과 같음. 템플릿 + 값 = 최종 spec.

### Step 2 — `semi-run init` (~3초)

Python CLI (`src/semi_design_runner/cli.py:56-91`)가:
1. **Pydantic strict validation**: spec.yaml이 schema 위반 시 즉시 reject (`RejectedNotInG1Scope`)
2. **S3에 spec 업로드**: `s3://$BUCKET/runs/$RUN_ID/staging/spec.yaml`
3. **DynamoDB Candidates 테이블에 메타 write**: ddb_write_count atomic increment (KG-E 측정)
4. **cost guard 검증**: `planned_cost_per_stage_usd` 합 > `compute_budget_usd` ($0.50)이면 `BudgetExceededError` (KG-F1)

> **비유**: pytest fixture 검증 + S3 push + 비용 알람.

### Step 3 — `semi-run submit` → AWS Step Functions 실행 (~30분)

CLI가 Step Functions를 trigger. SFN이 **5 stage 직렬 실행**:

```
rtl-build  →  synth       →  pnr            →  signoff   →  metrics
(elaborate)   (Yosys)        (LibreLane/        (DRC/LVS    (parse
                              OpenROAD)          /STA)        *.rpt)
```

각 stage는 **Fargate Spot task** (4vCPU/16GB/200GiB ephemeral). 도구 컨테이너는 `lockfile.yaml`에 pin된 ECR 이미지 사용.

### Step 4 — Artifact 수집 (~1초)

각 stage 종료 시 S3에 산출물 업로드 (Object Lock GOVERNANCE — 변경 불가):
```
s3://$BUCKET/runs/$RUN_ID/final/
├── reports/
│   ├── gcd-synth.rpt           # area, gate count
│   ├── gcd-sta.rpt             # WNS, TNS, slack
│   └── gcd-drc.rpt             # violation list
├── metrics.json                # 구조화된 지표 (area_um2, power_mw, max_freq_mhz, ...)
├── trace.jsonl                 # reasoning trace (각 stage decision)
└── provenance.yaml             # lockfile_sha + license matrix
```

### Step 5 — Kill Gate 판정 (Operator turn)

Operator가 결과를 검토:
- **KG-A pass?** lockfile 일치 + 동일 seed 재실행 시 hash 동일 → ✅
- **KG-B pass?** sign-off clean + DRC=0 + WNS ≥ 0 + ≤30분 + ≤$0.50 → ✅
- **KG-C/D/E**: SDK quota / Spot reclaim / DDB write count

가장 중요한 줄:
```
status: clean
sign_off_status: clean
metrics: { area_um2: 1247, power_mw: 0.31, max_freq_mhz: 250, wns_ns: 0.45 }
```

> **비유**: GitHub Actions의 "All checks have passed". DRC=0 = lint clean, WNS ≥ 0 = perf 회귀 없음.

### 실패 시 자동 분류 (Negative Result)

본 프로젝트는 *실패도 자산*. agent가 자동 분류:
- `NR-toolchain-drift` (lockfile 불일치) → code-author 위임
- `NR-determinism-fail` (재실행 hash 다름) → codex:rescue 호출
- `NR-execution-fail` (sign-off non-clean) → spec parameter 재조정 plan
- `NR-timeout` / `NR-budget-exceeded` / `NR-spot-reclaim` / `NR-trace-malformed`

### ✅ Chapter 5 후 알게 되는 것

- `make run` = Makefile substitute → semi-run init → SFN 5 stage → S3 artifact → KG 판정
- Object Lock GOVERNANCE로 산출물 immutable (re-run으로 덮어쓰지 못함)
- 실패 7 분류가 자동 분류되어 후속 plan trigger

**더 깊이**: [`docs/superpowers/plans/2026-05-10-g1-first-smoke.md`](../superpowers/plans/2026-05-10-g1-first-smoke.md) (현재 freeze 상태인 첫 smoke 실험 plan).

---

## Chapter 6 — 평가·결정·다음 단계 (5분)

마지막 chapter. 본 프로젝트가 *학술적으로* 무엇을 주장하고, 어떻게 결정하는지.

### 핵심 가설 5개 (논문 publish/kill 분기)

| 가설 | 무엇을 측정 | 임계값 (spec §5.4) | 비유 |
|---|---|---|---|
| **H1a** Finding reuse rate | iteration 반복에 따라 *과거 발견 재사용률 증가* | linear regression slope > 0, α=0.05, R² ≥ 0.3 + blinded audit N≥2 일치율 ≥80% | "AI가 학습할수록 같은 버그 두 번 만들지 않는가" |
| **H1b** Non-knob structural patch | 부록 C 제외 transform이 sign-off clean × seed×3 | **최소 3건** | "AI가 새 알고리즘 3개 작성, 3 seed에서 unit test 통과" |
| **H1c** Cold-start failure rate | 새 디자인 첫 N=10 runs 실패율 | ORFS-agent baseline 대비 *감소* | "신규 프로젝트 초기 빌드 실패율 감소" |
| **H2** 복리 효과 | gcd→ibex→aes 순차 H1c 음의 기울기 | slope < 0, α=0.05, R² ≥ 0.3 | "프로젝트가 쌓일수록 다음 프로젝트가 빨라짐" |
| **H3** Tertiary (reasoning trace) | 평가자 N≥5가 trace 읽고 채택/기각 이유 복원 | **Cohen's κ ≥ 0.6** + FM1~FM4 pass율 ≥50% + evaluator separation | "AI의 결정을 사람 5명이 *왜 그랬는지* 동의 가능" |

### Decision Table — publish / reframed-publish / kill (spec §5.3)

**R0 override**: H3 평가 무결성 위반 → **즉시 kill** (모든 행 무시)

| H1 pass 수 | H3 결과 | 결정 |
|---|---|---|
| ≥ 2개 | pass | **publish** (full) |
| ≥ 2개 | fail | reframed-publish (H1 중심) |
| 1개 | pass | reframed-publish (부분 H1 + process) |
| 1개 | fail | **kill** |
| 0개 | pass | reframed-publish (process 중심) |
| 0개 | fail | **kill** |

> **비유**: A/B 테스트의 *statistical significance + qualitative review* 동시 통과 모델. 효과 크기(H1) + 메커니즘 이해(H3) 둘 다 필요.

### 운영 주기 (Operator workflow)

본 프로젝트의 한 cycle:

```
1. Operator: spec 결정 또는 위임 task 정의 (CLAUDE.md "Before Non-Trivial Work" 5단계)
2. Agent: patch 또는 evidence 제안 (experiment-designer / code-author)
3. Operator: 검토 · 디버깅 · 머지 · 결정 승인
4. wiki/raw/: 결과(reasoning trace · finding · decision) 누적
5. wiki/ 컴파일: ingest → 다음 cycle context로 활용
6. Phase 0 학습 통찰: spec/wiki 갱신 후보 → co-evolution 1회전
```

### 현재 상태 (2026-05-25 기준)

| Gate | 상태 |
|---|---|
| G0 — Program bootstrap (K1+K2 evidence + overview spec) | ✅ complete |
| G1 — L1 Process (SHA-pinned + Fargate Spot + SFN) | 진행 중 (첫 smoke plan freeze, `g1-smoke-pre` tag @ commit `2be69ed`) |
| G2 — L2 Substrate (memory + skill_library + lint API) | pending (L1 후 병렬) |
| G3 — L3 Content (Open-Ideation + MLPerf 평가) | pending (License Gate §13 선행) |
| G4 — 통합 실험 + publish/kill 결정 | pending |

### 어떻게 기여하나 (외부 개발자)

본 프로젝트는 *single-operator*라 외부 contributor 머지는 받지 않지만, 다음 방식으로 학습/참여 가능:

- **읽기**: `INTENT.md` → 본 문서 → `docs/vibe-coding-tutorial/` (history) → `wiki/index.md` (knowledge)
- **dogfooding**: 본인 repo에서 `INTENT.md` + `.claude/agents/` + wiki-first 구조 채택
- **피드백**: GitHub issue (의도공학 layer 마찰 발견 시)
- **재현**: 6개월 후 published 결과가 나오면 본 repo clone → `make run` 재현

### ✅ Chapter 6 후 알게 되는 것

- 본 프로젝트의 publish/kill 분기는 H1×H3 매트릭스 + R0 override (H3 무결성 위반 시 즉시 kill)
- 운영 주기는 *Operator 결정 → agent 제안 → 머지 → wiki 누적 → 다음 cycle*
- 현재 G1 진입 중 (2026-05-10 첫 smoke plan freeze)

**더 깊이**: [`docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`](../superpowers/specs/2026-04-19-integrated-research-program-design.md) §5.3 + §5.4.

---

## 다 읽었다. 다음은?

| 관심 | 읽을 것 |
|---|---|
| **이 프로젝트가 어떻게 진화했나** (history) | [`docs/vibe-coding-tutorial/`](../vibe-coding-tutorial/) |
| **칩 설계 용어 더 자세히** | [`docs/glossary.md`](../glossary.md), [`wiki/eda-flow-report-reading.md`](../../wiki/eda-flow-report-reading.md) |
| **첫 smoke 실험 plan 자체** | [`docs/superpowers/plans/2026-05-10-g1-first-smoke.md`](../superpowers/plans/2026-05-10-g1-first-smoke.md) |
| **3-layer deep dive** | `~/.claude/plans/intent-md-l1-l2-l3-sorted-wozniak.md` (본 문서 작성 시 사용한 deep dive plan) |
| **Operator 운영 매뉴얼** | [`docs/onboarding.md`](../onboarding.md) |
| **의도공학(intent engineering) 사례 연구** | [`INTENT.md`](../../INTENT.md) (특히 §Learnings) |

### 본 문서의 한계

본 튜토리얼은 *수직 진입*(top-down)만 다룬다. 만약 본 프로젝트 코드에 *수평적*으로 패치를 가하고 싶다면:
1. `CLAUDE.md` "Before Non-Trivial Work" 5단계 먼저 수행
2. `INTENT.md` Not 섹션 정합 검사
3. spec 변경이 필요한가 → Codex 3-round review 필요
4. 4 agent 중 어느 것에 위임 가능한가 검토

본 프로젝트는 *문서 = 의도 = 운영의 일치*가 substrate라, 한 곳을 바꾸면 다른 곳도 같이 바꿔야 한다 — 이게 vibe-coding의 마찰 비용이자 power.
