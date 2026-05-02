# Research Agents Design — Operator Subagents + L3 Research Agent Skeletons

| | |
|---|---|
| 작성일 | 2026-05-02 |
| 작성자 | Jung Do Hyun (serithemage@gmail.com) |
| 상태 | Draft — 운영자 1차 승인 대기 (Codex 3-round는 본 spec 본문에서 보류; L3 §7 review의 일부로 흡수 가능) |
| 전제 spec | `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` (overview), `2026-04-23-L2-substrate-design.md`, `2026-04-26-L3-content-design.md` |
| 본 spec 범위 | (1) 운영용 Claude Code subagent 6종 신설, (2) L3 연구 에이전트 8종 skeleton (역할·계약·분리 규칙만), (3) 분리 규칙의 schema-level enforcement 3-layer |
| 본 spec 비범위 | L3 8종 prompt template 본문, tool manifest allowlist, validate-spec Lambda 코드, Codex 3-round 자체 — 모두 L1 G1 `.rpt` 실측 후로 보류 (overview·L3 spec이 명시한 일정 준수) |

---

## 1. 목적 (Why)

현재 repo는 다음 두 gap이 동시에 열려 있다.

1. **운영자 측 마찰**: spec 작성·`.rpt` 해석·LLM 생성 RTL 비판·lockfile bump·docker build 디버그·graphify 운영이 모두 운영자(이 repo 주인)의 손으로 in-line 처리되고 있다. 각 작업의 컨텍스트가 다르고 LLM 호출 패턴도 다르지만, 책임 단위가 분리되지 않아 한 세션이 여러 역할을 동시에 떠안는다.
2. **연구 측 stub**: L3 spec §3.1이 8종 에이전트의 추상화 레벨까지는 확정했으나, 본문(prompt template + tool manifest)은 L1 G1 `.rpt` 실측 후로 명시 보류했다. 그 사이 8종의 **역할·계약·분리 규칙**조차 코드/파일 형태로 존재하지 않아, L1이 끝나는 순간에 한꺼번에 잡아야 할 일이 누적된다.

본 spec은 두 gap을 **동시에**, 단 **각자의 boundary를 schema 수준에서 격리한 채** 채운다. 운영용은 즉시 가치(Task tool로 호출 가능), 연구 8종은 prompt 본문을 비워둔 채 역할·계약·분리 규칙만 담은 skeleton — L1 완료 시점에 본문만 채우면 즉시 가동.

## 2. Not (비목표)

- L3 8종의 prompt template 본문 작성 (overview·L3 spec 일정 위반)
- L3 8종의 tool manifest allowlist 확정 (동일)
- validate-spec Lambda 또는 provenance.yaml 런타임 enforcement 코드 (L3 §6.4 follow-up)
- 운영 subagent의 Codex 3-round review (본 spec은 운영자 1차 승인으로 freeze)
- Claude·Codex 외 다른 LLM SDK 통합 (overview §2 비목표 준수)

## 3. 디렉토리 구조 + 격리 경계

```
.claude/agents/                        ← Task tool에 자동 메뉴 등록 (사용자가 호출)
├── spec-architect.md
├── eda-report-reader.md
├── rtl-critic.md
├── lockfile-bumper.md
├── docker-build-debugger.md
└── kg-keeper.md

agents/research/                       ← Task tool 인덱스 밖 (Codex/Claude SDK가 file path로 읽어 system prompt로 사용)
├── README.md                          ← 책임 매트릭스 + 분리 매트릭스 + provenance schema
├── spec.md
├── architect.md
├── rtl.md
├── tb.md
├── verif.md
├── signoff.md
├── evaluator.md
└── planner.md

tests/agents/
├── test_separation_rules.py           ← 본 spec §6.2 매트릭스를 코드로 강제
└── test_research_isolation.py         ← .claude/agents/*.md가 agents/research/를 참조하지 않음을 검증
```

**격리 원칙**: `.claude/agents/`와 `agents/research/`는 **물리적으로 분리된 트리**다. 전자는 Claude Code Task tool이 자동 인덱스, 후자는 인덱스 외 — 운영자가 무심코 연구 에이전트를 in-process로 호출해 R0(role conflation, overview §6.2)을 위반하는 사고를 schema 수준에서 차단한다.

## 4. 운영 subagent 6종 (`.claude/agents/`)

각 파일은 frontmatter (`name`, `description`, `tools`, `model_family_default`) + body 구조를 따른다. body는 다음 5섹션 고정:

1. **언제 호출되는가** (description trigger 신호 상세)
2. **무엇을 받고 무엇을 출력하는가**
3. **사용 가능한 도구·금지된 도구**
4. **권고 LLM family와 그 이유**
5. **운영 룰** (직접 commit/push 금지, agents/research/ 접근 금지, R4 준수)

### 4.1 책임표

| Agent | description trigger | 주 도구 | 권고 LLM family | 출력 | 금지 |
|---|---|---|---|---|---|
| `spec-architect` | "spec 작성/수정", "derived spec", "Codex review 준비"; overview/L2/L3 정합성 검사 | Read · Write · Edit · Bash(git, grep) · graphify query | **Claude** (long-form structured writing); review는 codex-rescue plugin 위임 | `docs/superpowers/specs/YYYY-MM-DD-*.md` + 변경 diff 요약 | direct commit/push, `agents/research/` 접근 |
| `eda-report-reader` | ".rpt 해석", "STA slack", "DRC violation", `.rpt/.def/.sdc` 파일 등장 | Read · Bash(grep/awk on .rpt) · graphify query | **Codex** (cross-family from spec-architect — RTL/.rpt 해석은 Codex 강함) | "어떤 violation이 critical인가 + 어떤 .rpt 필드가 root cause" 한 페이지 진단 | RTL/패치 직접 수정 |
| `rtl-critic` | "RTL 리뷰", "Verilog/Chisel 비판적 읽기"; LLM 생성 RTL 입력 | Read · Bash(yosys-stat, slang) · graphify query | **Codex** (Claude가 만든 RTL을 Codex 렌즈로 — self-bias 회피) | top 3 risk + suggested patch 위치 (직접 수정 X) | 직접 RTL 수정·테스트 실행 |
| `lockfile-bumper` | "lockfile bump", "container_digests", "ECR digest fill", `lockfile.yaml` 수정 요청 | Read · Edit · Bash(gh API, aws ecr describe-images) · `semi-run lockfile-verify` | **Claude** (구조화 추적) | bump 후보 표 + verify 결과 + commit 메시지 초안 | direct commit/push (운영자 승인 필요) |
| `docker-build-debugger` | "ORFS/LibreLane docker build 실패", `docker/build-*.sh` 실패 로그, "image layer 디버그" | Read · Bash(docker build/run/logs/inspect) | **Codex** (긴 빌드 로그 grep·diff에 강함) | 실패 layer + 후보 fix 1-3개 (직접 수정 X) | Dockerfile 직접 수정 |
| `kg-keeper` | "graphify update/lint", "god node", "AMBIGUOUS triage", `make graph-*` | Read · Bash(`make graph-*`, `uv run graphify ...`) · graphify MCP | **Claude** | lint 결과 + AMBIGUOUS top N + suggested ingest | wiki/raw/* 직접 수정 |

### 4.2 공통 운영 룰 (모든 운영 subagent body 마지막 섹션 고정 문구)

> **이 에이전트는 제안만 한다. 다음 행위는 운영자의 명시적 추가 요청 없이 절대 수행하지 않는다.**
> - `git commit`, `git push`, `git rebase`, `gh pr create` (CLAUDE.md "Direct commits to main is the user's explicit workflow"와 정합)
> - `agents/research/` 하위 파일 read/write (운영↔연구 격리 — overview §6.2 R0)
> - `wiki/raw/`, `lockfile.yaml`, `cdk/`의 직접 수정 — 본인 책임 영역이 아닐 때

### 4.3 frontmatter 표준 (모든 운영 subagent 공통)

```yaml
---
name: <agent-name>
description: <trigger 신호 상세 — when, what input, what output. 직접 commit/push 금지 한 줄 포함>
tools: <Read, Edit, Write, Bash(...), graphify_query, ...>
model_family_default: <claude|codex>
---
```

`model_family_default`는 권고이며 강제 아님 — Task tool이 이 필드를 인지하진 않으므로 운영자가 호출 시 별도 모델 선택. body 첫 줄에 동일 권고를 한 번 더 명시.

## 5. L3 연구 에이전트 8종 skeleton (`agents/research/`)

### 5.1 파일 구조 (모든 L3 에이전트 공통)

각 `agents/research/<role>.md`는 정확히 5 섹션:

```markdown
# <Role>

## Role
<one-liner: 이 에이전트가 H1/H3 측정에 어떤 evidence를 기여하는가>

## Inputs (L1/L2 contract refs)
- L1: <overview §3.2 contract 항목 인용>
- L2: <L2.skill_library.query / L2.memory.recall 호출 패턴, L2 spec §5 인용>

## Outputs (consumer + schema 위치)
- consumer: <어떤 다른 agent가 이 output을 소비하는가>
- schema: <Pydantic 모델 위치 또는 .yaml frontmatter 키>

## Separation rules
- 같은 LLM instance 금지: <agent A>, <agent B>, ...
- 같은 LLM family 금지: <agent C> (R6 evaluator separation)
- provenance.yaml 4필드 필수: agent_id, llm_family, llm_version, parent_run_id

## Prompt template + tool manifest
<!-- TBD: L1 G1 `.rpt` 실측 후 별도 follow-up issue (L3 spec §3.2)에서 채움.
     본 skeleton 단계에서는 이 섹션을 placeholder 주석만 남기고 비워둔다. -->
```

### 5.2 책임 매트릭스 + 분리 매트릭스

| Agent | Role one-liner | 핵심 Input | 핵심 Output | **분리 금지 (instance / family)** |
|---|---|---|---|---|
| `spec` | candidate spec(YAML) 생성, `search_tier` 필드 강제 | `L2.memory.recall` evidence | `Spec` pydantic + `provenance.yaml` | instance ≠ Evaluator (R0 §6.2 #1) |
| `architect` | microarchitecture idea (Open Ideation Tier 2 진입점) | `L2.skill_library.query` skill 카탈로그 | reversible-patch 제안 (서명되지 않은 draft) | instance ≠ Evaluator |
| `rtl` | Architect idea → Verilog/Chisel | Architect output, Gemmini base RTL | `*.v` / `*.scala` patch | instance ≠ Verif (RTL이 자기 코드의 testbench 작성 시 self-test bias) |
| `tb` | testbench 생성 (DUT-blind: RTL interface 명세만 보고 작성) | RTL interface (DUT 내부 X) | cocotb / SystemVerilog TB | instance ≠ RTL |
| `verif` | cocotb / Verilator 시뮬 운영, coverage 산출 | RTL + TB | coverage report, fail trace | instance ≠ Signoff (커버리지 통과 ≠ sign-off 통과) |
| `signoff` | DRC/LVS/STA boolean 결정 | L1 `.rpt` artifact | `signoff_pass: bool` + slack/violation 표 | instance ≠ Evaluator (R0 §6.2 #2) |
| `evaluator` | H1/H3 rubric 채점 | L1 `reports[]` + reasoning trace | Cohen's κ rubric 결과 | instance ≠ Spec, instance ≠ Signoff, **family ≠ trace 생성 LLM family** |
| `planner` | Open Ideation candidate sampling 전략 | `L2.skill_library.query` 통계 + 부록 C exclusion | 다음 N candidate 우선순위 | instance ≠ Evaluator |

### 5.3 provenance.yaml 공통 hook

L3 에이전트 모든 invocation은 다음 4필드를 `provenance.yaml`에 emit한다 (스키마는 L3 spec §2.4 self-defined provenance 정렬):

```yaml
agent_id: <role>                # spec/architect/rtl/tb/verif/signoff/evaluator/planner
llm_family: <claude|codex|gemini|human>
llm_version: <model id>         # ex: claude-opus-4-7, codex-cli-1.x, human-doh
parent_run_id: <ULID>
```

이 4필드 누락 시 L1 sign-off 단계에서 reject — 본 spec은 schema만 명시하고 enforcement 코드는 §6.2 runtime check (TODO)에 위임.

### 5.4 `agents/research/README.md` 내용

`agents/research/README.md`는 본 spec §5.2 표 + §5.3 provenance hook을 그대로 인용하고, 추가로 다음 한 줄을 첫 줄에 명시:

> **WARNING**: 이 디렉토리의 파일은 Claude Code Task tool에서 직접 호출하지 않는다. Codex/Claude SDK가 외부 subprocess로 read하여 system prompt로 사용한다. Task tool에서 호출 시 R0 (role conflation) 위반 risk — `.claude/settings.json` PreToolUse hook이 경고를 emit한다 (본 spec §6.3).

## 6. 분리 규칙 enforcement (3-layer)

### 6.1 Static check (이번 구현 범위)

`tests/agents/test_separation_rules.py`:
- 모든 `agents/research/*.md`를 파싱해 `## Separation rules` 섹션의 금지 매트릭스가 본 spec §5.2와 byte-identical인지 비교
- 분리 규칙 섹션 누락 시 fail
- §5.3 provenance hook 4필드가 README에 명시되어 있는지 확인

`tests/agents/test_research_isolation.py`:
- `.claude/agents/*.md`의 어떤 파일도 `agents/research/`를 substring으로 포함하지 않음
- 운영 subagent 6종의 description 끝에 §4.2 공통 운영 룰 문구 ("이 에이전트는 제안만 한다. ...")가 포함되어 있음

### 6.2 Runtime check (TODO — L1 G1 `.rpt` 실측 후)

`validate-spec` Lambda(L3 spec §6.4)에 다음 검사 추가:
- provenance.yaml의 `(agent_id, llm_family)`가 §5.2 분리 매트릭스를 위반하면 reject
- `evaluator.trace_consumer`의 family ≠ `<trace_producer>.llm_family`

본 spec은 enforcement 코드를 작성하지 않고, **테스트 스켈레톤 + TODO 주석**만 남긴다. 사유: L3 spec이 ".rpt 실측 후" 보류로 명시했고, 본 spec은 그 일정을 침범하지 않는다.

### 6.3 PreToolUse hook (운영자 가드, 경고만)

`.claude/settings.json`에 추가:

```json
{
  "PreToolUse": [
    {
      "matcher": "Task",
      "hooks": [
        {
          "type": "command",
          "command": "echo \"$1\" | grep -q 'agents/research/' && echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"WARNING: Task prompt references agents/research/. L3 research agents must run via Codex/Claude SDK subprocess, not via Task tool — R0 (role conflation, overview §6.2) risk.\"}}' || true"
        }
      ]
    }
  ]
}
```

차단(block) 아님 — 경고만 inject, 운영자 판단 영역 보존 (R4 준수).

### 6.4 운영자 가드 — 자동 commit/push 금지

운영 subagent body §4.2 공통 운영 룰 문구로 강제. 추가로 hook은 만들지 않는다 (CLAUDE.md "Direct commits to main is the user's explicit workflow"가 이미 운영자 vision이라, 강제 hook은 운영자 자유 침해).

## 7. Out of scope 명시 (재확인)

- L3 8종 prompt template 본문 → L1 G1 `.rpt` 실측 후 별도 follow-up issue (L3 spec §3.2 / §8 issue #1)
- L3 8종 tool manifest allowlist → 동일
- validate-spec Lambda 코드 → L3 spec §6.4 follow-up
- Codex 3-round review → 본 spec은 운영자 1차 승인으로 freeze. L3 본문 합류 시 §7 통합 review에 흡수 가능
- 운영 subagent의 model 강제 (frontmatter `model` 필드) → `model_family_default`만 권고, 강제 X (운영자 호출 시 자유 선택)

## 8. 변경되는 기존 파일

| 파일 | 변경 |
|---|---|
| `.claude/settings.json` | PreToolUse hook 1개 추가 (§6.3) |
| `docs/architecture/2026-05-01-current-architecture.md` | §1 매트릭스 행 추가 ("운영 subagent 6 + L3 8종 skeleton" — 코드 표면 변화 반영). §6 placeholder는 그대로 |

## 9. 작업 순서 (writing-plans 분할 기준)

| Phase | 내용 | 의존 |
|---|---|---|
| R1 | 본 spec 작성 + 자체 review + 사용자 review | — (이 brainstorming 끝) |
| R2 | writing-plans로 implementation plan 분할 | R1 승인 |
| R3 | `agents/research/` 9개 작성 (분리 규칙 까다로움 — 먼저 freeze) | R2 |
| R4 | `tests/agents/` 2개 작성 → R3 회귀 방지 즉시 가동 | R3 |
| R5 | `.claude/agents/` 6개 + `.claude/settings.json` hook | R4 |
| R6 | `docs/architecture/...` 매트릭스 행 갱신, commit/push | R5 |

## 10. Risk / 대응

| Risk | 대응 |
|---|---|
| 운영자가 `agents/research/`를 Task tool로 호출하여 R0 위반 | §6.3 PreToolUse hook 경고 inject + §6.1 static test가 운영 subagent에서 참조 차단 |
| L3 8종 skeleton의 분리 매트릭스가 spec과 drift | §6.1 static test가 byte-identical 검증 — drift 발생 시 CI fail |
| 운영 subagent가 description-spam (Task tool 메뉴 혼잡) | 운영 6개로 제한 (브레인스토밍에서 "균형" 선택). 추가 subagent는 본 spec amendment로만 |
| LLM family 권고가 강제되지 않아 self-bias 발생 | body 권고문 + 운영 룰 + (장기) Codex 3-round 등 review 도입으로 보강. 본 spec 단계에서는 권고만 |
| L1 G1 `.rpt` 실측 전에 prompt template을 채우고 싶은 유혹 | §7 명시 + spec freeze로 차단. 본문 채움은 별도 spec amendment 절차 필요 |

## 11. Open questions (운영자 결정 영역, spec freeze 전 답변 필요)

| # | 질문 | 후보 |
|---|---|---|
| Q1 | `agents/research/`가 Task tool에 자동 포함되지 않는다는 것이 모든 Claude Code 버전에서 보장되는가? | 검증 필요 — 보장 안 되면 frontmatter `name`을 의도적으로 비워 메뉴 등록 차단 |
| Q2 | `model_family_default` frontmatter 필드를 Claude Code가 인지하는 표준 필드로 사용해도 되는가? | 비표준이면 body 권고만으로 운영 |
| Q3 | PreToolUse hook이 Task의 prompt 텍스트를 `$1`로 받는 contract는 안정적인가? | settings.json 문서 재확인 필요 |

→ Q1·Q2·Q3는 본 spec 승인 후 R5 phase 진입 직전에 검증. fail 시 R5 design 조정.
