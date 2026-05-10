# 신규 참여자 가이드 (Operator용)

> **이 프로젝트는 Operator 1명이 다중 에이전트를 감독·운영하는
> single-operator multi-agent 구조다.** 신규 진입자 = Operator. Researcher /
> Developer 역할은 에이전트가 수행한다. 따라서 본 가이드는 *세 사람의 분기*가
> 아니라 *Operator 한 사람의 세 감독 채널*을 다룬다.
>
> 정확한 설계 근거는 항상 `wiki/index.md` (default 라우팅) 와
> `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`
> (overview spec — single source of truth) 를 따른다. 모르는 용어는
> [`docs/glossary.md`](glossary.md) 옆에 두고 읽는다.

## 1. 이 프로젝트는 무엇인가 (15분 요약)

**Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator
Design**. 한 줄로 — *EDA 도구가 만든 리포트와 실행 trace를 근거로 LLM
에이전트가 작은 실험을 반복하고, 사람(Operator)이 감독하는 연구 프로그램.*

### 3-layer 구조 (연구 프로그램의 층)

| Layer | 역할 | 비유 |
|---|---|---|
| L1 Process | 재현 가능한 실행 환경 (SHA-pinned Nix + AWS Fargate Spot + Step Functions) | *부엌* |
| L2 Substrate | 지식·메모리 (`.rpt` / patch / 결정을 typed-frontmatter로 축적) | *레시피 노트* |
| L3 Content | 실제 연구 대상 (Gemmini, MLPerf Tiny v1.3 streaming, Open-Ideation DSE) | *오늘 만들 음식* |

같은 인프라를 *4-plane* (Local · AWS · Tool · Knowledge) 시각으로도 봄.
두 시각은 overview spec §3에서 동시에 정의된다.

### 현재 위치 — G0 → G1 전환 단계

| Gate | 내용 | 상태 |
|---|---|---|
| **G0** | Program bootstrap (K1 52 + K2 61 sources + overview spec + 위키 ingest) | ✅ complete |
| **G1** | L1 Process bootstrap (`make run` gcd SFN 완주 + KG-A~KG-E 통과) | pending — L1 파생 spec |
| G2 | L2 Substrate (typed-frontmatter memory + skill library) | pending |
| G3 | L3 Content MVP (Gemmini DSE, gcd/ibex/aes) | pending |
| G4 | 통합 실험 + 논문 figure (overview spec §5.3 publish/reframed/kill) | pending |

### 무엇이 *novel*한가 (publish 축)

**Process novelty + 학술 contribution**, 상용 칩 대비 절대 PPA 아님. 가설:
- **H1** — report memory + reversible-patch skill library가 (a) finding 재사용, (b) 구조적 patch, (c) cold-start 실패 측면에서 ORFS-agent baseline 대비 개선.
- **H2** — 디자인 순차 누적 시 복리 효과 (보조 지표).
- **H3** — 비전문가가 reasoning trace를 읽고 채택·기각 이유 *복원* 가능 (LLM-as-judge κ ≥ 0.6).

가설 자체가 *Operator 운영 모델의 정당성*을 검증하는 명제다 — 다음 §2 참조.

## 2. 운영 모델 — Operator 1명 + 에이전트

본 프로젝트엔 사람이 *한 명*이다. 코드 작성·리서치·spec draft·wiki ingest는
모두 *에이전트에게 위임*되며, Operator는 *결정 · 검토 · 디버깅 · 학습*을
담당한다.

| 감독 채널 | 누가 수행 | Operator의 책임 |
|---|---|---|
| **학습 채널** | Operator 자신 | Phase 0 Q&A로 EDA 운영자 감각 축적 — `.rpt` 해석, 파일 포맷, LLM 출력의 함정 |
| **Researcher 채널** | 에이전트 (Claude Code · Codex SDK · plugin skills) | 위임 task 정의, 에이전트 출력의 spec 인용 sanity, source 누락 짚기, 결정 승인 |
| **Developer 채널** | 에이전트 (code-reviewer / code-simplifier subagent 포함) | 위임 task 정의, 코드 리뷰, commit 컨벤션 검사, 머지 결정 |

### 왜 이 구조인가

H1/H2/H3 가설 자체가 *"비전문가 Operator가 에이전트를 감독해 칩 설계 연구를
수행 가능한가"*다. 본 운영 모델은 단순 노동 분배가 아니라 **가설 검증
설계의 일부** — Operator의 학습 곡선, 에이전트 출력 디버깅 빈도, 머지 거절
사유가 모두 *evidence*로 누적된다 (§11 참조).

### 따라서 새 작성자(=Operator)의 첫 통과 의례

1. *내가 직접 하는 영역*과 *에이전트에게 위임할 영역*의 경계 감각 잡기.
2. 학습 채널을 가장 먼저 확보 — 에이전트 출력을 검수할 수 없으면 운영 모델이 무너진다.
3. 위임 도구 (Claude Code 세션, Codex CLI, plugin skills) 환경 점검.

## 3. 환경 준비 (Operator 1회, 약 15분)

```bash
# 1) clone + 의존성 설치
git clone <repo-url> semiconductor-design
cd semiconductor-design
make install                    # uv sync --all-extras

# 2) sanity check (Operator가 직접 돌림)
make test                       # pytest -v
make lint                       # ruff check src tests scripts

# 3) 위키 첫 통독
$EDITOR wiki/index.md           # default 라우팅 hub
$EDITOR docs/glossary.md        # 모르는 용어 옆에 두기
```

전제: **Python 3.12 + [uv](https://docs.astral.sh/uv/)**. 다른 도구 (Nix, AWS,
LibreLane) 는 *해당 layer에 들어갈 때*만 필요. 첫주엔 위 3개로 충분.

위임 환경: Claude Code CLI (또는 IDE 확장) + Codex SDK + 본 리포의 plugin
skills (`documentation:llm-wiki`, `pr-review-toolkit:*`,
`semi-design-learning` 등). CLAUDE.md "Before Non-Trivial Work" 5단계가 *위임
task 정의 시 에이전트가 따라야 할 순서*를 명시.

## 4. Operator 첫주 — 세 감독 채널

### 4.1 학습 채널 (Operator가 직접 — Phase 0)

```
1. docs/learning/phase-0-curriculum.md
   → "관점 전환" 섹션. 이 4줄(읽기 우선·파일 포맷·리포트 해석·상용 vs 오픈)이
     본 프로젝트 학습 lens 전체를 압축.

2. wiki/phase-0-eda-operator-lens.md  (policy 페이지)
   → Branch A 4 concept 페이지로 라우팅:
     [[cmos-fundamentals]] → [[digital-logic-gates]]
       → [[clock-and-timing]] → [[fsm-and-pipeline]]

3. wiki/eda-flow-report-reading.md
   → Yosys / OpenROAD / LibreLane 3.0.2 / sky130A 4단 리포트 operator
     시점 진입점. *.rpt 해석이 본 프로젝트 핵심 능력.

4. wiki/pdk-file-formats.md
   → Liberty .lib / LEF / DEF / SDC 포맷이 EDA 도구 간 lingua franca.

5. 첫 학습 세션 시작 — assistant-led Q&A
   → semi-design-learning skill로 sub-topic 진행. 결과는
     wiki/raw/sessions/phase-0-<code>-<slug>.md 에 원문 저장.
     이 노트들이 누적되면 documentation:llm-wiki ingest로 위키 페이지가
     컴파일된다.
```

이 채널은 *위임 불가* — 에이전트 출력의 함정을 찾으려면 Operator 자신이 감각을 갖춰야 한다.

### 4.2 Researcher 채널 (에이전트에게 위임 → Operator는 검토)

**Operator가 에이전트에게 시킬 첫 task 후보**:

```
- "overview spec §1-§5 읽고 H1/H2/H3 falsifier 요약 + §5.3 canonical
  decision table을 표로 재진술해라"
- "wiki/k1-{α,β,γ,δ}-evidence + wiki/k2-{ε,ζ,η,θ}-evidence 통독 후
  K1 source가 K2 spec 결정으로 어떻게 cascade되는지 [[link]] 그래프로 정리"
- "wiki/raw/imports_manifest.yaml 정찰 → decision_anchors top 10 추출 +
  spec_contradictions 분류"
- "K2 ε 4 deferred items가 L2-substrate-design spec §5.1을 어디서
  미커버하는지 grep + 보고"
```

**Operator 검토 책임**:
- 출력의 spec 인용이 정확한지 *직접 grep* (`grep -n '§5.3' docs/superpowers/specs/2026-04-19-*.md`).
- source 누락·왜곡 짚기 (특히 `wiki/raw/papers/`의 critical_read 표시 source).
- 결정 승인 — wiki ingest, spec 갱신은 *에이전트 제안 → Operator 머지* 흐름.

**위임 도구**: `documentation:llm-wiki` skill (5단계 ingest 워크플로),
`pr-review-toolkit:code-reviewer` (spec doc 리뷰에도 적용 가능),
Codex CLI (`/codex:rescue` for second-opinion review).

### 4.3 Developer 채널 (에이전트에게 위임 → Operator는 코드 리뷰)

**Operator가 에이전트에게 시킬 첫 task 후보**:

```
- "make install / test / lint pass 확인. 실패하면 root cause + 수정 patch"
- "src/semi_design_runner/cli.py 진입점 구조 요약 + 테스트 커버리지 보고
  (현재 ≥85% target 충족 여부)"
- "scripts/graph_integrity_check.py 동작 트레이스 — orphan / dangling /
  AMBIGUOUS 검사 로직 + 두 JSON 포맷(NetworkX vs graphify-native)
  처리 분기 설명"
- "issues/{001~005}.md를 layer/gate별로 정리 + L1 파생 spec 작성에
  blocker가 되는 이슈 식별"
```

**Operator 검토 책임**:
- 코드 리뷰 — `pr-review-toolkit:code-reviewer` subagent로 1차 + Operator 2차.
- commit 컨벤션 검사 — `docs(wiki)` / `docs(spec)` / `chore` / `feat` / `fix` / `test` prefix, 한국어 본문, imperative subject.
- 머지 결정 — *직접 commit*은 Operator만 (에이전트는 patch 제안 단계까지).
- 의도 부합 검사 — 에이전트가 자신의 추측으로 spec 의미를 바꾸지 않았는가.

**위임 도구**: `pr-review-toolkit:code-reviewer` /
`pr-review-toolkit:code-simplifier` / `pr-review-toolkit:silent-failure-hunter`
/ `pr-review-toolkit:type-design-analyzer` subagent, Codex CLI rescue.

## 5. 자주 쓰는 명령

| 명령 | 용도 |
|---|---|
| `make install` | uv sync --all-extras |
| `make test` | pytest -v |
| `make lint` / `make fmt` | ruff check / format (`src tests scripts`) |
| `uv run pytest tests/test_X.py::test_y -v` | 단일 테스트 |
| `make graph-update` | graphify AST 증분 (LLM 비용 0) |
| `make graph-serve` | graphify MCP 서버 (L2.memory.recall 백엔드) |
| `make graph-lint` | graph integrity check (L2.lint.check) |
| `uv run graphify query "..."` | BFS 질의 (보조 path 탐색) |
| `make kg-all-smoke` | G1 kill-gate aggregator (offline synthetic, AWS 없이) |

위키 작업은 `documentation:llm-wiki` skill 명령 (`init` / `ingest` / `query`
/ `lint` / `sync` / `export` / `qmd-index` / `lancedb-sync`)을 사용한다 —
이 skill은 Operator가 직접 호출하거나 에이전트 세션에서 위임된다.

## 6. 진입 지도 (Repository map)

| 경로 | 한 줄 |
|---|---|
| `README.md` | program overview + Knowledge base 정책 + Layer 분리. 첫 진입 정상화. |
| `CLAUDE.md` | 에이전트 협업 규칙. **Operator는 위임 task 정의 시 본 파일의 "Before Non-Trivial Work" 5단계를 그대로 인용**. |
| `docs/glossary.md` | 용어집 (12살용 풀이 + 비유). 모르는 단어 즉시 조회. |
| `docs/onboarding.md` | **이 문서**. |
| `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` | **overview spec — single source of truth**. |
| `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` | L2 substrate 파생 spec. |
| `docs/superpowers/plans/` | per-phase TDD 구현 plan. |
| `docs/knowledge-base/2026-04-19-k1-direction-report.md` | K1 종합 방향 판단. |
| `docs/learning/phase-0-curriculum.md` | Phase 0 마인드맵 + 진행 상태. |
| `wiki/index.md` | 위키 라우팅 hub (default 컨텍스트). |
| `wiki/{slug}.md` | 컴파일 페이지 (concept · policy · synthesis · decision · entity). |
| `wiki/raw/**` | 불변 seed corpus. |
| `src/semi_design_runner/` | L1 Process Python CLI. wheel 진입점. |
| `scripts/graph_integrity_check.py` | L2.lint.check substrate. |
| `scripts/inject_freshness.py` | graphify 노드 freshness 주입. |
| `tests/` | pytest. tmp_path + fixture 패턴. |
| `issues/` | local 이슈 트래커 (5 open). frontmatter는 layer/gate/blocks 명시. |
| `graphify-out/` | 보조 path 쿼리 산출물. |
| `Makefile` | 모든 표준 명령 정의. |
| `pyproject.toml` | uv 의존성 + ruff 설정 (100 char, py312) + script entrypoints. |

## 7. 작업 컨벤션 (요약)

- **Direct commits to `main`** — 현재 워크플로 (no feature branches).
- **Conventional commit prefix**: `docs(wiki)`, `docs(spec)`, `docs(glossary)`, `chore`, `feat`, `fix`, `test`. Subject는 imperative.
- **본문 한국어, slug/identifier는 English** — wiki page slug은 Obsidian `[[link]]` 호환을 위해 영어/하이픈.
- **에이전트 작성 commit은 `Co-Authored-By:` trailer 포함** (모델 식별 명시).
- **답변·문서 작성 시 `[[wiki/페이지]]` 인용 강제** (CLAUDE.md L13 wiki-first 정책).
- **테스트는 `tmp_path` + fixture** — 실제 `wiki/raw/`는 절대 건드리지 않는다.
- **Coverage target**: `src/semi_design_runner/` ≥ 85% per module.
- **Ruff 100 char line limit, `target-version = "py312"`**, `src tests scripts` 모두 lint/fmt 대상.
- **Reversible patch 정신** — baseline 직접 덮지 말고 patch 단위로 (overview spec §7 operating rules).

## 8. 막힐 때 — 어디서 묻는가

| 막힘 종류 | 첫 진입 |
|---|---|
| 모르는 용어 | `docs/glossary.md` |
| 개념·페이지 라우팅 | `wiki/index.md` → `[[link]]` 2-hop 확장 |
| 프로그램-수준 결정 | overview spec `2026-04-19-integrated-research-program-design.md` (특히 §3.2, §5.3, §6.2, §13) |
| L2 substrate 결정 | `2026-04-23-L2-substrate-design.md` |
| 미해결 fork (open decision) | `issues/README.md` |
| Phase 0 학습 진행 상태 | `docs/learning/phase-0-curriculum.md` (마인드맵 체크박스) |
| 에이전트 협업 규칙 | `CLAUDE.md` |
| spec ↔ source 의존성 (cross-component) | `make graph-serve` MCP 또는 `uv run graphify query "..."` |
| 에이전트가 같은 실수를 반복 | memory 파일 (`memory/feedback_*.md`) 확인 + 부족하면 새 entry 추가 |

## 9. 에이전트에게 위임할 작업 후보 (Pending 영역)

각 항목은 *Operator가 task를 정의 → 에이전트가 patch 제안 → Operator가 검토·머지* 흐름.

| 영역 | 어느 채널 | 시작점 |
|---|---|---|
| **L1 파생 spec** (G1) | Researcher | overview spec §6 + K2 ζ evidence + KG-A~KG-E |
| **L2 파생 spec 갱신** (G2) | Researcher | `2026-04-23-L2-substrate-design.md` + K2 ε 4 deferred items |
| **L3 spec** (G3) | Researcher | overview spec §13 License Gate 선행 + K2 θ evidence |
| **K2 ingest 결과 spec 갱신** | Researcher | wiki K2 evidence 4 페이지 → §6.2 lockfile / §13 License Gate / §3.2 contracts 갱신 |
| **위키 새 페이지 컴파일** | Researcher | wiki/index.md "Pending Compile" (B branch HDL · KG-E DDB · Si2 Liberty · Cadence LEF/DEF · OpenSTA 등) |
| **graphify cross-link 정제** | Developer | `docs/graphify/cross-links.md` (bridge manifest), `make graph-lint` 통과 유지 |
| **이슈 해소** | 둘 다 | `issues/{001~005}.md` 각 layer/gate 매핑 후 작업 |
| **L1 코드 boilerplate** | Developer | `src/semi_design_runner/` 확장 (`semi-run` CLI 분기, AWS 클라이언트 wrapper) |

Operator가 "이번 주는 어디 위임할까"를 결정할 때 본 표 + `issues/README.md`
를 함께 본다.

## 10. Layer 경계 — 헷갈리지 말 것

본 프로젝트엔 **두 개의 독립 layer**가 있다.

1. **사람·LLM 컨텍스트 라우팅** (wiki-first hybrid, 2026-05-09부)
   - 답변 작성 시 `wiki/index.md` → `[[wiki-link]]` 우선.
   - graphify는 cross-component path 보조.
   - 본 onboarding 가이드와 glossary는 *이 layer*에 작용.

2. **Agent system 내부 API** (graphify backend, spec-frozen)
   - `L2.memory.recall` / `L2.skill_library.query` / `L2.lint.check`.
   - 이 셋은 overview spec §3.2 + L2-substrate-design §5.1에서 *graphify backend로 spec-freeze*.
   - 변경은 L2 spec-owner의 Codex 3-round review 필수.

이 둘을 섞으면 "wiki-first 정책이 agent 내부 API도 wiki로 바꾸자고 한다"는
잘못된 결론으로 이어진다. **wiki-first는 사람용, graphify는 agent 내부.**
두 결정은 독립이다.

## 11. 운영 모델 자체가 가설 검증 데이터

본 가이드 §2의 *Operator 1명 + 에이전트* 운영 모델은 단순 워크플로가 아니라
**이 프로젝트가 평가하려는 H1/H2/H3 가설의 직접 검증 대상**이다.

따라서 다음이 모두 evidence로 누적된다:

| 누적되는 것 | 어디에 |
|---|---|
| Operator의 Phase 0 학습 곡선 | `wiki/raw/sessions/phase-0-*.md` (불변 원본) → 컴파일 페이지 |
| 에이전트에게 위임한 task 정의 | `wiki/raw/sessions/` 또는 git commit 메시지 본문 |
| 에이전트 출력 디버깅 횟수·사유 | reasoning trace (G2 substrate 도착 후) + memory 파일 (`memory/feedback_*.md`) |
| Operator의 머지 거절 사유 | git history (revert / amend 거절) + commit message |
| 에이전트의 false positive 패턴 | `memory/feedback_*.md` 누적 → wiki 컴파일 |

→ **개별 작업 단위가 모두 본 가설의 데이터 포인트**. 단순 productivity가
아니라 *연구 contribution의 일부*로 다룬다는 자각이 본 프로젝트의 메타
원칙.

---

> 더 깊이 들어가려면 `wiki/index.md` 의 "라우팅 규칙" 4단계와 `CLAUDE.md` 의
> "Before Non-Trivial Work" 5단계를 동시에 참조한다. 둘이 본 가이드의 압축
> 버전이다.
