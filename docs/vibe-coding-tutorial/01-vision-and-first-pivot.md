# Chapter 01 — 비전과 첫 pivot

> **시간**: 2026-04-17 11:46 ~ 2026-04-19 23:00 (약 60시간 wall clock, 8-10시간 active)
> **AWS 비용**: $0.00
> **핵심 인사이트**: 도전적 비전을 한 번에 정의하지 마라. 첫 prompt → brainstorming → 첫 코드 → 1차 pivot 사이클을 빠르게 돌려라.

## 맥락

반도체 설계는 이 사람의 본업이 아니었다. 본인 표현으로 *"PyTorch나 CUDA는 직접 다루지 못하지만 AWS상에서의 ML Pipeline에 대해서는 상당한 전문성을 갖추고 있음"*. 그러나 LLM agent를 잘 쓰면 이런 격차도 메울 수 있겠다는 가설로 출발했다. 이 chapter는 그 가설이 어떻게 brainstorming 1회와 archived spec 1회를 거쳐 *오픈소스 EDA + AutoResearch 기반의 학술 novelty 프로그램*으로 재정의되었는지 추적한다.

## 첫 prompt

```
AI를 활용해서 딥러닝 학습이나 추론에 사용할 반도체를 설계하고 싶어.
먼저 이러한 에이전트 기반 연구 프로젝트에 참고할만한 리소스가 있는지
퍼플렉시티로 조사해서 보고해.
```

— 2026-04-17 10:46

세션 0281a7f3가 시작됐다. Claude는 perplexity MCP로 다음 16개 사례를 보고했다 (요약):

- **OpenROAD-Agent (2024)** — RTL→GDS LLM-driven flow.
- **EvolVE (2026)** — non-knob 구조 패치 evolutionary search.
- **MAGE (2024)** · **VerilogCoder (AAAI 2025)** · **AssertLLM (ASP-DAC 2025)** — multi-agent HDL.
- **AutoDMP (NVIDIA ISPD 2023)** · **PTPT/RankTuner/MO-TuRBO** — BO autotuning baseline.
- **CircuitNet 2.0 (ICLR 2024)** — 데이터셋.
- **Cadence/Synopsys/Siemens copilots** — commercial reference.
- **Karpathy AutoResearch (2025)** — "agent가 reproducible한 ML 실험을 자동으로 수행" 패턴.

이 보고서가 두 번째 prompt의 형태를 만들었다.

## 두 번째 prompt — 도전 수준 협상

사용자는 superpowers의 `brainstorming` skill에 들어갔다. brainstorming skill은 사용자에게 4단계의 도전 수준을 묻는다 (A: MVP DSE / B: agent reasoning trace / C: 학술 novelty / D: production chip).

```
에이전트를 통해서 비전문가가 반도체 설계에 대해서 단기간에 학습하고
프로덕션 가능성이 있는 결과물을 만들어 내는 도전적인 목표를 세웠어.
따라서 D가 목표야.
```

— 11:21

Claude는 D-목표(production-grade chip)의 비현실성을 정량적으로 회신했다: 7nm 이하 공정 접근 불가, 수억 USD 단위의 mask cost, sign-off 검증의 인력 비용. 사용자는 한 단계 내려와 현실적 표현을 찾았다.

```
A와 B 중간임. 프로젝트 수행자는 PyTorch나 CUDA는 직접 다루지 못하지만
AWS상에서의 MLPipeline에 대해서는 상당한 전문성을 갖추고 있음.
https://github.com/roboco-io/serverless-autoresearch 를 참조해.
```

— 11:26

이 한 문장에 본 프로젝트의 **3대 제약**이 모두 들어있다:

1. **사람 능력 한계**: PyTorch/CUDA 직접 작성 X. 즉 RTL/EDA 코드를 *읽고 검수* 가능한 수준이 목표지, *작성*하는 것이 목표가 아니다.
2. **사람 능력 자산**: AWS ML pipeline 전문성. 즉 인프라 코드는 사용자가 잘 검토 가능하므로 보수적 패턴(SHA-pin, IaC, observability)을 fully expand해도 좋다.
3. **외부 reference**: `serverless-autoresearch` repo. AutoResearch 패턴을 자기 도메인에 적용 가능하다는 신호.

## A → 도전 수준 1 단계 상승

```
일단 A로 하고 완료후 다음 이터레이션에서 다시 결정해 보자.
```

— 11:29

```
좀 더 도전적으로 진행하자. 인프라는 AWS 서버리스 아키텍처를 적극 활용해줘.
https://github.com/roboco-io/serverless-autoresearch 를 참조해.
```

— 11:33

A로 한 번 정했다가 4분 만에 "좀 더 도전적으로"로 자기 수정. 이 작은 미세 조정 사이클은 이후 11일 내내 반복된다 — *"먼저 하나 가보고 다음 iteration에서 다시 결정"*. spec을 한 번에 완벽하게 쓰려 하지 않는다.

## 기술 스택 결정 — 4문장

```
LLM은 Claude Code SDK와 Codex SDK를 사용해줘. 나는 AWS 테크니컬 트레이너
출신이라 DDB 좋아함. 스텝평션 오케스트레이션도 당연히 선호함. IaC는 CDK사용해줘.
```

— 11:41

```
CDK는 타입스크립트로
```

— 11:43

이 4문장만으로 본 프로젝트의 모든 인프라가 fix됐다 — Claude Code SDK + Codex SDK (LLM), DynamoDB (DDB), Step Functions (SFN), CDK TypeScript (IaC). 이 결정은 이후 한 번도 번복되지 않았다.

`★ Insight ─────────────────────────────────────`
- 인프라 결정은 "선호 표현"으로 충분 — *"DDB 좋아함"*에서 spec § "DDB 4 tables"가 자연스럽게 도출. 연구 프로젝트는 인프라 선택의 객관적 정당성을 요구하지 않는다.
- 외부 repo(`serverless-autoresearch`) 1개 명시가 spec 절반을 결정 — Claude가 그 repo의 구조(Step Functions Map → Fargate Spot)를 그대로 본 프로젝트에 transplant.
- "트레이너 출신"은 단순 자기소개가 아닌 *"내가 검수 가능한 영역과 불가능한 영역의 경계"* 신호 — agent 입장에서 프롬프트 해석에 직접 사용.
`─────────────────────────────────────────────────`

## 4/17 오후 — 첫 코드 + 첫 archived spec

같은 날 사용자는 `superpowers:writing-plans` skill로 Phase 1a 계획을 만들고, `superpowers:subagent-driven-development` skill로 wiki engine 코드를 7-8 commits로 작성했다 (`5f63ffc..b077888`). 이때의 코드:

```
src/semi_design_wiki/
├── __init__.py
├── frontmatter.py          # YAML frontmatter parser
├── init.py                 # idempotent wiki dir initializer + CLI
├── reindex.py              # atomic index rebuilder grouped by page type
├── lint.py                 # broken links, orphans, frontmatter, confidence checks
└── ...
```

이 코드는 5일 후 (4/22) 통째로 폐기된다. 사용자가 Phase 1a wiki 엔진을 직접 만드는 대신 외부 도구 `graphify`를 발견했기 때문이다 (chapter 04). 100+ commits의 프로젝트에서 *코드의 25%가 폐기되는 것*은 vibe coding의 정상적인 진화 패턴이다.

### 🔧 Debugging: "초기 spec을 너무 길게 쓰면 archived 1번 → 2번 → ... 사이클이 생긴다"

**증상**: 4/17 첫 spec(`semiconductor-design-agent-design.md`)이 2일 후인 4/19에 *완전히* archive됨. 약 30 KB 분량 spec이 "stale gates 다수"로 retain only for history.

**근본 원인**: 첫 prompt 시점에 OpenLane2 → LibreLane rename 정보가 spec에 미반영. Efabless가 2025-02 셧다운한 사실 미인지. MLPerf Tiny v1.2가 v1.3으로 갱신된 것 미인지. 모두 사용자가 외부 자료를 충분히 적재하지 않은 채 spec을 먼저 썼기 때문.

**Fix**: 4/19에 *"지식 기반 우선 원칙"*을 명시적 user feedback으로 등록 (chapter 02). 그 후 작성된 spec(`2026-04-19-integrated-research-program-design.md`)은 4/22에 K2 갱신을 한 번 더 받았지만 *archive되지 않고 계속 진화*했다.

**시간 소실**: 약 6시간 (Phase 1a 코드 일부 + 첫 spec 작성).

**교훈**: spec을 쓰기 *전에* 외부 자료를 충분히 ingest. 사용자가 4/19에 등록한 메모리:

> [지식 기반 우선 원칙](memory/feedback_knowledge_first.md) — spec·MVP 결정 전 최신 자료·논문을 wiki에 ingest, 방향 판단은 그 이후

## 4/17 저녁 — Phase 0 학습

```
Phase0로 일반 개발자가 이 프로젝트를 수행하기 위해서 필요한 지식들을
마인드맵에서 가지를 뻗어나가듯이 하나하나 Q&A를 통해 학습하고 이를 문서화, 스킬화 해줘.
```

— 13:50

A1 (CMOS) → A2 (logic gates) → A3 (clock·timing) → A4 (combinational/sequential) 순서의 학습 세션이 시작됐다. 매 세션은:

1. Claude가 5-10줄 explanatory text로 시작
2. 사용자가 *"다음"* 또는 follow-up 질문
3. 세션 끝나면 `wiki/raw/sessions/phase-0-aN-*.md`에 기록

이 패턴은 이후 *graphify가 자동 인덱싱*해서 향후 "MOSFET이란?" 같은 질문에 그 학습 세션을 직접 가져올 수 있게 했다.

```
1. IJK 브랜치가 뭐야? 2. a로 해줘
```

— 13:54

A4 마지막에 사용자가 마인드맵 IJK 가지(I=Yosys, J=OpenROAD, K=LibreLane)에 대해서 빠르게 묻고 결정. 이 한 줄로 학습 커리큘럼 6개 가지 중 IJK를 *"compact만 학습"*으로 표시.

### 🔧 Debugging: "2nm 공정은 누설을 어떻게 해결했어?"

**증상**: 4/17 23:16에 사용자가 2nm 공정의 leakage 처리 방법을 묻자, Claude는 GAA(Gate-All-Around) FET, BSPDN(Backside Power Delivery Network), high-NA EUV 등을 정확히 답변. 그러나 이 깊이의 답변이 *오픈소스 EDA + sky130A* 시나리오와 어떻게 연결되는지 사용자가 다음 문장으로 명시할 때까지 알 수 없었다.

**근본 원인**: Phase 0 학습이 일반 반도체 깊이 vs EDA operator 운영 깊이 사이에서 표류.

**Fix**: 4/19에 사용자가 강한 feedback을 줌:

> Phase 0는 **EDA operator로서 agent를 supervise/debug**할 수 있는 수준이 목표지, chip designer를 만드는 것이 아님. RTL 비판적 읽기, `*.rpt` 파일 해석, 파일 형식(`.v/.lib/.lef/.def/.sdc`) 이해를 우선. 깊은 이론은 리포트 해석이 막힐 때만.

이 feedback이 메모리로 들어가고, A1-A4의 깊이가 retroactive하게 압축됐다. Curriculum의 B/D/E (반도체 일반)는 compact화, C(EDA flow)와 F(PDK formats)는 elevated.

**시간 소실**: 약 2시간 (A3-A4의 일부가 retroactive 재정의).

## 4/17 밤 — Output style 변경 + handoff skill 신설

```
Set output style to Learning
```

— 23:48

`/config`로 output style을 Learning으로 변경. 이 style은:

- `★ Insight ─────────` 마커로 educational 코멘트 강제
- 20+ 줄 코드 작성 시 사용자에게 2-10줄 Learn-by-Doing 위임
- 사용자 결정이 필요한 trade-off는 항상 inline 표시

이 style 변경이 본 튜토리얼의 *형태*를 결정한다. 이후 모든 chapter의 코드 commit이 학습용 anchor를 가지게 됐다.

같은 날 자정 직전:

```
어떤 작업을 진행하다가 잠깐 다른걸 하고 와야 하는 경우에, 컨텍스트가 이어질 수
있도록 루트에 .handoff.md 문서로 맥락을 일시 저장하는 기능을 전역 스킬로 만들어줘.
세션 시작시에 .handoff.md를 확인하고 있을경우 진행, 진행 후에는 삭제.
```

— 23:51

→ `~/.claude/skills/handoff` 스킬 신설. 본 프로젝트 11일간 *11번* 호출됐다 (`/handoff save` ↔ `/handoff resume` 사이클). multi-session 컨텍스트 유지가 본 프로젝트 진행의 *operational backbone*이 됐다.

## 4/18 — Phase 0 A1, A2 마무리

이날은 학습 세션 + commit 2건만:

```
570575f docs(phase-0): Q&A session for A1 transistor·CMOS + mark A1 complete
beb0ba6 docs(phase-0): Q&A session for A2 logic gates + mark A2 complete
```

각 세션 1-2시간. 사용자는 코딩 0줄, 학습 prompts만 입력했다.

## 4/18 늦저녁 — 첫 pivot

```
나는 오픈소스 EDA와 바이브 코딩 기법을 이용해서 실험적인 딥러닝 학습 또는
추론용 칩 아아디어를 도출하고, AWS 인프라 위에서 Karpathy 의 AutoResearch같은
방법을 적용시켜서 검증하는 방법으로 상용대비 의미있는 아웃풋을 내고 싶어
```

— 22:50

이 한 문장이 4/17 spec(*"AI agent로 반도체 설계"*)을 4/19 spec(*"오픈소스 EDA + 바이브 코딩 + AutoResearch + 학술 novelty"*)으로 재정의한다. 표면적으로 비슷해 보이지만 차이는 결정적이다:

| 4/17 spec | 4/19 pivot |
|---|---|
| **목표 산출물** | "production-feasible chip" | "academic/process novelty vs commercial chips" |
| **PPA 비교 대상** | TPU/H100 등 commercial silicon | gcd/ibex/aes의 자체 baseline (template DSE) |
| **검증 기준** | 상용과의 절대 비교 | publish/reframed/kill을 §5.3 canonical decision table로 |
| **공정 가정** | 7nm 이하 | sky130A (130nm OpenPDK) |
| **EDA 가정** | mixed (commercial + open) | open source only — Yosys/OpenROAD/LibreLane |
| **Reference** | OpenROAD-Agent | serverless-autoresearch + AutoResearch + EvolVE |

```
c 혼합으로 가되, 상용/오픈소스 EDA의 핵심적인 개념만 빠르게 이해하는 쪽으로
학습방향을 잡아줘
```

— 22:58

EDA 학습은 *"compact, operator-lens"*로 압축.

## 4/19 — `/init` + brainstorming v2

```
/init
```

— 04:56

Claude가 `CLAUDE.md`를 자동 생성. 이때 만들어진 `CLAUDE.md`는 11일간 5회 갱신되며 진화하지만, 4/19에 첫 골격이 잡혔다.

```
@docs/eda_agent_handoff.md 를 읽고 계획을 다시 세워줘
```

— 05:01

이전 세션의 `docs/eda_agent_handoff.md` (ORFS autotuning 단독 MVP를 가정한 핸드오프)을 read해서 brainstorming v2 시작. 결과: ORFS-agent (2025) 존재로 autotuning 단독 MVP 가정이 무효 → 통합 프로그램으로 진화.

```
사용자에게 입력을 요구할때는 AskUserQuestionTool을 사용하도록 글로벌 규칙을 추가해줘.
```

— 05:04

이 한 줄로 사용자 글로벌 규칙(`~/.claude/CLAUDE.md`) 첫 줄이 결정됐다. 본 프로젝트 11일간 AskUserQuestion이 *수십 회* 호출되며 옵션 선택 / 승인 / 의도 확인 / 디자인 결정의 표준 인터페이스가 됐다.

```
코덱스로 계획 리뷰하고 지적사항을 알려줘.
```

— 20:24

처음으로 Codex가 reviewer로 등장. Codex는 본 프로젝트에서 4-5회 위임받아 spec 3-round 리뷰 / lockfile placeholder 결정 / structure review 등을 수행했다. 항상 *독립 시각*으로 — Claude의 생각을 모르는 상태에서 의견을 주는 reviewer 역할.

## 결과: 4/19 끝 시점 상태

| 자산 | 상태 |
|---|---|
| 첫 spec (4/17) | archived |
| Integrated overview spec (4/19) | 작성 중 (다음 chapter) |
| Phase 0 학습 세션 | A1-A4 완료, IJK 가지 compact 결정 |
| Phase 1a wiki 코드 | 8 commits 완료 (이후 4/22 폐기 예정) |
| superpowers skill 채택 | brainstorming · writing-plans · subagent-driven-development · TDD · debugging |
| 글로벌 규칙 등록 | "AskUserQuestion 사용", "Learning output style" |
| 신설된 user skill | `handoff` (multi-session 컨텍스트) |
| Memory 등록 | "프로젝트 핵심 의도" + "EDA operator 학습 lens" |

## Try It Yourself

본 chapter를 따라하려면:

```bash
# 1. brainstorming skill 진입 — 도전 수준 협상
claude  # in any project repo
> /brainstorm

# 2. handoff skill 신설 — 본 chapter에서 만든 글로벌 skill
mkdir -p ~/.claude/skills/handoff
# (skill 정의는 본 repo의 `.claude/skills/handoff/SKILL.md` 참조)

# 3. Learning output style 활성화
> /config
> # 화살표로 Learning 선택

# 4. Phase 0 마인드맵 세션 시작 — semi-design-learning skill 활용
> 학습 재개

# 5. 첫 spec을 archived로 두는 패턴 — 디렉토리 분리
mkdir -p docs/superpowers/specs/archived
git mv docs/superpowers/specs/2026-XX-XX-old-spec.md docs/superpowers/specs/archived/
```

### Running cost (chapter 누적)

| Phase | 항목 | 비용 | 누적 |
|---|---|---|---|
| Setup | brainstorming + 첫 spec 작성 | $0.00 | $0.00 |
| Phase 0 | A1-A4 학습 세션 (사람 시간 8h, AWS 0) | $0.00 | $0.00 |
| Pivot 1 | spec archive + integrated 방향 결정 | $0.00 | $0.00 |
| **Total ch01** | | **$0.00** | **$0.00** |

LLM 토큰 사용량은 별도 집계하지 않는다 (개인 plan 기준).

### Timeline

- 04-17 10:46 — 첫 prompt
- 04-17 11:21 — 도전 수준 D 제시 → 11:33 A → 11:33 "더 도전적으로" 재조정
- 04-17 11:41 — 기술 스택 4문장 fix
- 04-17 13:50 — Phase 0 학습 시작
- 04-17 22:50 — 첫 spec 작성 (archived 예정)
- 04-17 23:48 — Learning output style 활성화
- 04-17 23:51 — handoff skill 신설 prompt
- 04-18 종일 — Phase 0 A1/A2
- 04-18 22:50 — *첫 pivot* "오픈소스 EDA + 바이브 코딩 + AutoResearch"
- 04-19 04:56 — `/init` (CLAUDE.md 첫 생성)
- 04-19 05:04 — AskUserQuestion 글로벌 규칙
- 04-19 20:24 — Codex 첫 위임

다음 chapter는 *"지식 기반 우선 원칙"*이 정식 등록되고 K1 4축 52 sources를 적재하면서 통합 프로그램 spec이 어떻게 생성되었는지 다룬다.
