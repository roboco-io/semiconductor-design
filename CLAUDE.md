# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This repo is an **AI agent research project**, pivoted **2026-05-29** to:
**"AutoResearch 기반 EDA Surrogate 모델 자동 연구"**.

karpathy [AutoResearch](https://github.com/karpathy/autoresearch)의 population-based evolution 루프
([roboco-io/serverless-autoresearch](https://github.com/roboco-io/serverless-autoresearch) HUGI 패턴)를
**EDA surrogate 지표예측 모델**(합성 직후 feature → 최종 PPA/routability 예측) 학습에 적용한다.
에이전트는 학습 스크립트 한 파일(`train.py`)만 변형하고, 고정 예산으로 학습 후 단일 val 지표로
keep/discard하며, **객관적 자동 게이트(median + T1 검증)가 winner 승격을 판정**한다(2026-06-08 재피벗).

- **목표**(2026-06-08 재피벗): 절대 PPA가 아니라 **(1) 비전문가 empowerment + 큰 흐름의 이해가능성**
  — 자율 진행을 기본으로 하되 사람은 *방향타이자 학습자*(per-winner 승인 아님), **(2) (연기) reasoning trace**
  라는 접근성/프로세스 축의 novelty. (구 "Operator-in-loop authority" 축은 INTENT 재피벗으로 대체됨.)
- 설계 lineage(brainstorming 전문): [`docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md`](docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md)
- 제품 요구: [`PRD.md`](PRD.md) (4-엔티티 ERD + 리포지토리 구조의 single source).
- 이전 의도/구현(통합 프로그램 3-layer L1/L2/L3)은 **`archive/integrated-program-3layer` 브랜치에 무손실 보존**.
  main에는 더 이상 존재하지 않으며, 새 작업의 근거로 삼지 않는다.

## Intent

본 프로젝트의 *Why · What · Not · Learnings* 는 [`INTENT.md`](INTENT.md) 에 정리되어 있다
(**status: exploring**, 2026-05-29 피벗 재작성). 메타 목적 두 가지 —
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

피벗 직후 **골격 단계** — placeholder만 존재하고 구현은 plan 승인 후 착수.

| 항목 | Scope | Status |
|---|---|---|
| 피벗 설계 + ERD | 설계 spec + `PRD.md` (4-엔티티 ERD) | ✅ commit `e631e79`·`5e361aa` |
| main 골격 재편 | serverless-autoresearch 정렬 디렉터리 + placeholder | ✅ `prepare.py`/`train.py`/`program.md`/`config.yaml` 골격 |
| 구 3-layer 보존 | wiki K1+K2 113 sources, CDK, agent system 전량 | ✅ `archive/integrated-program-3layer` (로컬+원격) |
| `prepare.py` 구현 | EDA flow 1회 → feature+label 데이터셋 (frozen, 사람 유지) | ⏳ plan 대기 |
| `train.py` 구현 | surrogate 학습 (에이전트 변형 단일 파일) | ⏳ plan 대기 |
| 진화 루프 (src/pipeline) | candidate_gen · batch_launcher · result_collector · selection | ⏳ plan 대기 |
| (연기) reasoning trace | reasoning_trace·decision·finding 증거 평면 | 2차 세대 |

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

**리포지토리 구조 (serverless-autoresearch 정렬)**:
- `prepare.py` — EDA 데이터셋 준비 (**read-only / frozen** — 에이전트 변경 금지, 공정 비교 보장).
- `train.py` — surrogate 학습 (**에이전트가 변형하는 단일 파일**, 신규 의존성 금지, 고정 예산).
- `program.md` — 에이전트 baseline 지시문. `config.yaml` — AWS/파이프라인 설정.
- `src/pipeline/` — orchestrator · candidate_gen · batch_launcher · result_collector · selection.
- `src/sagemaker/` — training entry / wrapper. `data/raw/` — 데이터 참조(실데이터는 S3).
- `experiments/` — 세대별 리포트. `models/` — 학습 artifact.

**데이터 모델 (최소 4-엔티티)**: `DATASET ─< GENERATION ─< CANDIDATE ─< JOB`,
`CANDIDATE ─< CANDIDATE`(parent self-ref, crossover). 속성 표는 `PRD.md` §4.

**4-step 루프**: Candidate Generation → Batch Launch(병렬 Spot) → Result Collection → Selection,
세대 winner는 **자동 게이트(median + T1) 통과 시** git tag `gen-NNN-best`(전환 전까지 Operator가 게이트 확인 후 머지).

## Code Conventions

- **Direct commits to `main`** is the user's explicit workflow (no feature branches for now).
- **Conventional commit prefixes**: `docs: ...`, `chore: ...`, `test: ...`, `feat: ...`. Keep subject imperative.
- **Tests**: pytest; use `tmp_path` and fixtures. Never touch real data/artifacts in tests.
- **Ruff 100 char line limit**, `target-version = "py312"`.
- 에이전트가 작성하는 코드 변경은 `INTENT.md` `Not` 정합 검사를 통과해야 하며, **객관적 게이트 통과 후
  머지**한다(auto-gate 미구현 동안은 Operator가 게이트 확인 후 머지 — 임시).

## Repository Map (non-obvious parts)

- `docs/superpowers/specs/2026-05-29-autoresearch-eda-surrogate-pivot-design.md` — **THE** active 설계 spec
  (brainstorming 6문항 + Perplexity grounded positioning + 4-엔티티 ERD). non-trivial 변경 전 필독.
- `PRD.md` — 제품 요구 + ERD + 리포 구조 single source.
- `INTENT.md` — Why/What/Not/Learnings (status: exploring). 피벗 이전 6 Learnings 는 archived 하위 섹션에 보존.
- `prepare.py` / `train.py` — 현재 `raise NotImplementedError("skeleton: 구현 plan 승인 후 작성")` placeholder.
- `issues/` — 열린 결정 트래커 (피벗 후 재생성). PRD §10 Open Decisions(OD-1~5)를 추적. 설계 fork는 spec에 인라인하지 말고 issue로. OD-1(지표)이 나머지의 선행.
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
- **AI 도구 grounding 검증**: `*research*` 모델(Perplexity Sonar Deep Research 등)이 web search empty 시
  학습 distribution에서 confabulate. **응답 수신 직후 first check = citation 개수**.
  citation 0 → 응답 *전체 거부* + `*search*` 도구로 재조회. `*search*` 도구는 grounded가 기본.

## Before Non-Trivial Work

1. **`INTENT.md` 정합 점검** — 착수 전 `Not` 섹션 위반 여부 확인. 이게 모든 작업의 1차 gate.
2. **`PRD.md` + 설계 spec 조회** — ERD/구조 질문은 `PRD.md`, 결정 근거/positioning 은 설계 spec §1·§8.
3. 구 3-layer 자산이 필요하면 `archive/integrated-program-3layer` 브랜치에서 참조(복원 아님).
4. **맹목적 자율 금지** — 객관적 게이트(median + T1) 없이 main 자율 머지 금지. 자율 자동 승격이 목표이나
   auto-gate 미구현 동안은 Operator가 게이트 리포트 확인 후 머지(2026-06-08 재피벗 — 구 "Operator authority" 대체).
5. 본 프로젝트는 **AutoResearch surrogate 모델 학습의 자동 연구**이지, parameter sweep 단독(ORFS-agent 영역)이 아니다.
