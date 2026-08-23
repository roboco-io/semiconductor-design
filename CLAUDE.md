# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This repo is an **AI agent research project**, pivoted **2026-07-13** to:
**"자율 에이전트 산출물 자동 승격 거버넌스의 도메인-불문 일반성 실증"**.

EDA surrogate 사이클(사례 연구 1, 2026-05-29~07-10)에서 실증된 **4단 게이트 권력분립**
(median 선발 → LOGO 일반화 probe → 사전 고정 paired 통계 검정(T1) → 독립 엔진(Codex) 의미 심사)이
도메인-불문 거버넌스 패턴인지 실증한다. 도메인 A = **알고리즘 성능 최적화**: 에이전트가
`domains/algo-opt/solver.py` 단일 파일을 변형, 지표=벤치 실행시간(정합성 테스트 통과 전제),
그룹=워크로드 패밀리(dev/holdout/sealed 분할), 로컬 실행(AWS 비용 0). **컨트롤 후보 2종
(known-good/known-bad) 사전 등록 + 자율 5세대 + 사전 등록 사후 감사**로 H-G1(게이트 일반성)·
H-G2(발견의 일반성)를 판정한다. 판정 방향과 무관하게 사전 고정 기준대로 내려진 판정 자체가 산출물.

- **THE active spec**: [`docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md`](docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md)
  — 판정 기준(§5)은 사전 고정, 사후 변경 금지. 결정 경로: [`issues/008-pivot-direction.md`](issues/008-pivot-direction.md).
- **사례 연구 1 (EDA surrogate — 완결·frozen 보존)**: gen-001~008 + v2 encoder 기각(negative result).
  lineage spec: [2026-05-29](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md) ·
  [2026-07-02](docs/superpowers/specs/2026-07-02-frozen-encoder-representation-redesign-design.md) ·
  [`PRD.md`](PRD.md) (4-엔티티 ERD — 도메인-중립이라 새 사이클에도 유효).
- 이전 의도/구현(통합 프로그램 3-layer L1/L2/L3)은 **`archive/integrated-program-3layer` 브랜치에 무손실 보존**.
  main에는 더 이상 존재하지 않으며, 새 작업의 근거로 삼지 않는다.

## Intent

본 프로젝트의 *Why · What · Not · Learnings* 는 [`INTENT.md`](INTENT.md) 에 정리되어 있다
(**status: exploring**, 2026-07-13 피벗 재작성). 메타 목적 두 가지 —
(1) 의도공학(intent engineering) 패러다임 우수성의 사례 연구,
(2) Operator 학습 ↔ 프로젝트 진화의 co-evolution.
**본 CLAUDE.md 의 모든 컨벤션·작업 규칙은 `INTENT.md` 의 `Not` 섹션을 어긴 의사결정을 차단하는 substrate로 작동**한다.
새 spec/결정·task 정의 시 `INTENT.md` 와 정합하는지 먼저 점검한다. 학습이 누적되면 `INTENT.md` Learnings 에 기록 →
의도가 진화하고, 진화한 의도가 다시 spec·결정을 변형시키는 co-evolution 사이클이 본 프로젝트의 publishing 축.
(status가 clarified → exploring 으로 *되돌아간 것 자체*가 co-evolution 신호 — INTENT.md Learnings #1.)

## Operating Model

**Operator 1명 + 에이전트** single-operator multi-agent 구조. 사용자는 **Operator(방향타·학습자)** —
Researcher/Developer 역할은 에이전트가 수행하고, **winner 승격은 객관적 자동 게이트(median + T1)가 판정**한다.

> **전환 중(2026-06-08 재피벗)**: 목표는 *자동 게이트 통과 시 자동 승격*. 단 **auto-gate 코드는 아직
> 미구현**(operator_gate→auto-gate 전환은 별도 spec). 그때까지는 **Operator가 게이트 리포트를 확인하고
> 머지**한다 — 단, 이는 *권한 행사*가 아니라 *자동화 미완에 따른 임시 단계*다. 에이전트는 게이트
> (median + T1) 없이 main에 자율 머지하지 않는다(새 INTENT Not "맹목적 자율 금지").

> **⚠️ 위임 agent rework 대기**: `.claude/agents/*.md` 의 4 agent
> (`experiment-designer` · `experiment-runner` · `code-author` · `eda-code-reviewer`)는
> 피벗 이전 **EDA flow / Gemmini DSE / KG-A~E gate** 를 전제로 작성돼 **현재 stale**.
> 피벗 구조(prepare/train/세대 루프)에 맞춘 재정의 전까지 활성 분업 매트릭스로 신뢰하지 않는다.
> `.claude/skills/semi-design-learning/` (Phase 0 학습 skill) 도 같은 사유로 stale.

## Implementation Status

**2026-07-13 피벗 직후** — 새 사이클(도메인 A)은 spec 승인 완료, 구현은 plan 승인 후 착수.

| 항목 | Scope | Status |
|---|---|---|
| 피벗 spec (거버넌스 일반화) | 브레인스토밍 Q&A 5문항 + positioning 31 citation + 판정 기준 사전 고정 | ✅ Codex 게이트 approve (block 8건 반영) |
| issue 009 — 알고리즘 태스크 선정 | 도메인 A 벤치 태스크 (선정 기준 spec §4) | ⏳ open |
| 어댑터 층 + `domains/algo-opt/` | 4콜백·벤치 스위트·정합성 테스트·guard 확장 | ⏳ 구현 plan 대기 |
| 컨트롤 후보 2종 | known-good/known-bad 사전 등록 | ⏳ 구현 plan 대기 |
| 도메인 A 자율 5세대 + 사후 감사 | H-G1·H-G2 판정 | ⏳ |
| 도메인 B (LLM 프롬프트 진화) | 별도 spec | ⏳ A 판정 후 |
| **사례 연구 1 (완결·frozen)** | `prepare.py`(4설계 7,194행)·`train.py` B0·진화 루프 gen-001~008·pretrain/ v2(encoder 2회 기각 종결) | ✅ read-only 보존 |

## Commands

```bash
make install   # uv sync --all-extras
make test      # pytest -v
make lint      # ruff check
make fmt       # ruff format
make clean     # drop caches/build artifacts
```

Python 3.12, `uv`-managed. `pyproject.toml` 은 name `semi-design`, version `0.2.0`,
optional-deps `pipeline`(boto3/pydantic). 구 `semi_design_runner` wheel/entry points 제거됨.

## Architecture (big picture)

`PRD.md` 가 authoritative — 아래는 요약.

**리포지토리 구조**:
- `domains/algo-opt/` — **새 사이클(도메인 A)**: `solver.py`(에이전트 변형 단일 파일)·벤치 스위트·
  측정 하니스·정합성 테스트·컨트롤 후보 (solver.py 외 전부 frozen).
- `src/pipeline/` — 4단 게이트 체인(orchestrator · candidate_gen · runner · selection · validation ·
  guard · promotion_reviewer). 통계 코어는 도메인-중립 — 어댑터 콜백 4개로 도메인 주입(spec §4).
- `prepare.py` / `train.py` / `pretrain/` / `models/encoder-v1.pt` — **사례 연구 1, 전량 frozen**
  (에이전트 변경 금지; encoder는 참조도 금지 — 가드 차단).
- `program.md` — 에이전트 baseline 지시문(도메인 A용 아날로그는 구현 plan에서).
  `config.yaml` — 파이프라인 설정.
- `experiments/` — 세대별 리포트(EDA `gen-NNN` + 새 `algo-gen-NNN`·`algo-audit`). `models/` — 학습 artifact.

**데이터 모델 (최소 4-엔티티)**: `DATASET ─< GENERATION ─< CANDIDATE ─< JOB`,
`CANDIDATE ─< CANDIDATE`(parent self-ref). 도메인-중립 — DATASET은 새 사이클에서 "벤치 스위트"로
일반화. 속성 표는 `PRD.md` §4.

**4-step 루프**: Candidate Generation → Launch(도메인 A는 로컬) → Result Collection → Selection,
세대 winner는 **게이트 체인(median → LOGO → T1 → Codex) 전 단계 통과 시** git tag.

**세대 완료 후 튜토리얼(필수 마무리 단계)**: `generation.json`이 생긴 직후 **`experiment-tutorial` 스킬**로
`experiments/<도메인>-gen-NNN/README.md`(12살 눈높이 튜토리얼)를 생성한다. "신뢰가능한 자율"의
이해가능성 요소 산출물이므로 결과 정리·커밋 전에 항상 포함한다.

## Code Conventions

- **Direct commits to `main`** is the user's explicit workflow (no feature branches for now).
- **Conventional commit prefixes**: `docs: ...`, `chore: ...`, `test: ...`, `feat: ...`. Keep subject imperative.
- **Tests**: pytest; use `tmp_path` and fixtures. Never touch real data/artifacts in tests.
- **Ruff 100 char line limit**, `target-version = "py312"`.
- 에이전트가 작성하는 코드 변경은 `INTENT.md` `Not` 정합 검사를 통과해야 하며, **객관적 게이트 통과 후
  머지**한다(auto-gate 미구현 동안은 Operator가 게이트 확인 후 머지 — 임시).
- **frozen 목록**: (사례 연구 1) `train.py` B0·`prepare.py`(변경 금지), `pretrain/`·`models/encoder-v1.pt`
  (변경·참조 금지 — 가드 차단), 커밋된 dataset. (새 사이클) 도메인 A 벤치 스위트·측정 하니스·컨트롤
  후보·sealed 패밀리 정의 — 에이전트 변경 금지, 후보의 벤치 경로 참조는 가드가 실행 전 무효 처리.

## Repository Map (non-obvious parts)

- `docs/superpowers/specs/2026-07-13-agent-promotion-governance-pivot-design.md` — **THE** active 설계 spec
  (피벗 Q&A 5문항 + grounded positioning 31 citation + 판정 기준 §5 사전 고정). non-trivial 변경 전 필독.
- `docs/superpowers/specs/2026-05-29-...` · `2026-07-02-...` — 사례 연구 1 lineage spec (EDA 피벗·v2 재설계).
- `PRD.md` — 4-엔티티 ERD + 리포 구조 single source (EDA 서술은 사례 연구 1 맥락으로 읽을 것).
- `INTENT.md` — Why/What/Not/Learnings (status: exploring). 사례 연구 1 Learnings(2026-05-29~07-10)와
  3-layer 시절 Learnings는 하위 섹션에 무손실 보존.
- `prepare.py` / `train.py` — 사례 연구 1 구현 (frozen — 변경 금지).
- `issues/` — 열린 결정 트래커. 008(피벗 방향 — decided A), 009(알고리즘 태스크 선정 — open).
  설계 fork는 spec에 인라인하지 말고 issue로.
- `.claude/agents/*.md`, `.claude/skills/semi-design-learning/` — **stale, rework 대기** (위 Operating Model 참조).
- 구 3-layer 자산(wiki·graphify·CDK·`src/semi_design_runner`·issues·learning curriculum)은
  **`archive/integrated-program-3layer` 브랜치에만** 존재. main에서 찾지 말 것.

## Operating Invariants

운영 중 발견된 *시간 layer* 마찰 — 이를 어기면 같은 실패가 반복된다 (출처: `INTENT.md` Learnings).
**피벗과 무관한 메타 패턴이라 보존**한다 (substrate 참조는 stale여도 invariant는 유효).

- **Agent definition staleness**: `.claude/agents/*.md` · `.claude/skills/*` · `.claude/settings.json` 변경
  *직후 같은 세션*에서는 변경된 정의가 활성화되지 않는다. 신규 agent type 호출 시 `Agent type 'X' not found`.
  **세션 재시작 후 재호출이 default**. (피벗 agent rework 시에도 적용 — dogfooding은 재시작 다음 turn부터.)
- **추측 vs grep 검증**: 정합 작업(link 검증·citation 정합) 전 *반드시 grep으로 사실 확인*. 추측을 advisory에 기록 금지.
- **INTENT 권한 vs spec 권한 분리**: `INTENT.md` / 신규 plan 은 설계 spec 의 정량 임계값을 *복사 인용*만,
  *재정의 금지*. 위반 시 plan 즉시 reject. (현재 surrogate 지표 임계값은 데이터셋 확정 후 spec에 nail down 예정.)
- **AI 도구 grounding 검증**: 웹 조사는 **exa MCP**(`web_search_exa` / `web_fetch_exa`)를 사용한다
  (Perplexity는 2026-08-22부로 제거 — 사용 금지). 어떤 도구든 research형 응답이 web search empty 시
  학습 distribution에서 confabulate할 수 있으므로 **응답 수신 직후 first check = citation/URL 개수**.
  citation 0 → 응답 *전체 거부* + 검색 도구로 재조회.

## Before Non-Trivial Work

1. **`INTENT.md` 정합 점검** — 착수 전 `Not` 섹션 위반 여부 확인. 이게 모든 작업의 1차 gate.
2. **`PRD.md` + 설계 spec 조회** — ERD/구조 질문은 `PRD.md`, 결정 근거/positioning 은 설계 spec §1·§8.
3. 구 3-layer 자산이 필요하면 `archive/integrated-program-3layer` 브랜치에서 참조(복원 아님).
4. **맹목적 자율 금지** — 객관적 게이트 체인 없이 main 자율 머지 금지.
5. **사후 기준 변경 금지** — spec §5 판정 기준·감사 체크리스트는 결과 확인 전 고정. 변경은 새 spec의
   brainstorming→Codex 게이트로만 (v2 교훈).
6. 본 프로젝트는 **승격 거버넌스의 일반성 실증**이지, 빠른 알고리즘(SOTA)이나 EDA surrogate 재도전이 아니다.
7. **frozen 자산 존중** — Code Conventions frozen 목록 참조 (사례 연구 1 전량 + 도메인 A 벤치·하니스·컨트롤).

## LLM Wiki 활용 규칙

이 프로젝트는 `wiki/` 디렉토리에 `[[wiki-link]]` 교차참조 위키를 유지한다. Karpathy LLM Wiki 패턴을 따른다.

### 작업 시 우선순위

1. **위키 우선 참조**: 질문에 답하거나 작업을 시작할 때, `wiki/index.md`에서 관련 페이지를 먼저 찾아 읽는다. `[[wiki-link]]`를 따라 2-hop까지 확장하여 맥락을 파악한다.
2. **출처 인용**: 답변 작성 시 위키 페이지를 `[[페이지 제목]]` 형태로 인용한다.
3. **위키에 없으면 명시**: 위키에 답이 없으면 "위키에 없음"이라 표기하고 `wiki/raw/` 또는 외부 원본을 읽어 보강한다. 새 내용이면 `llm-wiki ingest`로 위키를 성장시킨다.
4. **검색보다 컴파일**: 매번 원본을 다시 읽지 말고, 이미 컴파일된 위키 지식을 적극 재활용한다.

### 위키 구조

- `wiki/index.md` — 자동 재빌드되는 라우팅 레이어 (수동 편집 금지)
- `wiki/{page}.md` — 컴파일된 지식 페이지 (`[[wiki-link]]` 교차참조)
- `wiki/raw/` — 원본 소스 드롭존 (불변)
- `wiki/log.md` — ingest 이력
- `wiki/.lancedb/` — 선택적 벡터 인덱스 (lancedb-sync 실행 시)

### 스킬 명령

사용자가 `llm-wiki <command>`를 호출하면 해당 단계 실행:
- `init` — 구조 초기화
- `ingest <source>` — 새 소스를 컴파일해 위키 갱신
- `query <질문>` — 하이브리드 검색(qmd) 또는 INDEX.md 라우팅
- `lint` — 끊어진 링크·고아 페이지 탐지
- `sync` — index.md 재빌드
- `export <template>` — 온보딩·ADR 요약 등 출력
- `qmd-index` — qmd 인덱스 빌드 (선택)
- `lancedb-sync` — LanceDB 벡터 인덱스 동기화 (선택)
