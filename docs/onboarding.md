# 신규 참여자 가이드

> 이 문서는 본 리포지토리에 처음 들어오는 사람을 위한 *역할별 진입 지도*다.
> 정확한 설계 근거는 항상 `wiki/index.md` (default 라우팅) 와
> `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md`
> (overview spec — single source of truth) 를 따른다.
> 모르는 용어는 [`docs/glossary.md`](glossary.md) 옆에 두고 읽는다.

## 1. 이 프로젝트는 무엇인가 (15분 요약)

**Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator
Design**. 한 줄로 — *EDA 도구가 만든 리포트와 실행 trace를 근거로 LLM
에이전트가 작은 실험을 반복하고, 사람(operator)이 감독하는 연구 프로그램.*

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

상세 hypothesis · falsifier · publish/kill 분기는 overview spec §4-§5.3 참조.

## 2. 본인이 어디에 속하는지 정하기

세 역할은 *상호 배타적이지 않다* — 한 사람이 두 역할을 겸할 수 있다.
다만 *첫날 진입 경로*는 다르다.

| 역할 | 이런 사람을 위한 경로 |
|---|---|
| **Operator** | EDA 운영자 렌즈로 학습하면서 에이전트 출력을 감독·디버깅하고 싶은 사람. Phase 0 학습이 출발점. 단독 진입 가능. |
| **Researcher** | K1/K2 evidence 위에서 spec을 작성·갱신하고, 위키에 새 ingest를 더하는 사람. overview spec과 evidence cascade가 출발점. |
| **Developer** | `src/semi_design_runner/` CLI · `scripts/graph_integrity_check.py` 같은 코드 layer를 만지는 사람. `make install` → `make test` → `pyproject.toml`이 출발점. |

## 3. 환경 준비 (모든 역할 공통, 약 15분)

```bash
# 1) clone + 의존성 설치
git clone <repo-url> semiconductor-design
cd semiconductor-design
make install                    # uv sync --all-extras

# 2) sanity check
make test                       # pytest -v
make lint                       # ruff check src tests scripts

# 3) 위키 첫 통독
$EDITOR wiki/index.md           # default 라우팅 hub
$EDITOR docs/glossary.md        # 모르는 용어 옆에 두기
```

전제: **Python 3.12 + [uv](https://docs.astral.sh/uv/)**. 다른 도구 (Nix, AWS,
LibreLane) 는 *해당 layer에 들어갈 때*만 필요 — 첫날엔 위 3개로 충분.

## 4. 역할별 첫날 계획

### Operator 경로

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
```

학습 결과가 누적되면 `documentation:llm-wiki` skill의 `ingest`로 위키 페이지가 컴파일된다.

### Researcher 경로

```
1. docs/superpowers/specs/2026-04-19-integrated-research-program-design.md
   → overview spec §1-§5. 목표, 4-plane × 3-layer, 가설(H1/H2/H3),
     §5.3 canonical decision table. Codex 3-round review 통과한
     authoritative 문서.

2. docs/knowledge-base/2026-04-19-k1-direction-report.md
   → K1 4축 52 sources의 종합 방향 판단. spec 결정의 출발점.

3. wiki/k1-{alpha,beta,gamma,delta}-evidence.md
   → K1 evidence 4 페이지. 각 frontmatter sources / related_specs로
     spec ↔ source 의존성이 명시됨.

4. wiki/k2-{epsilon,zeta,eta,theta}-evidence.md
   → K2 evidence 4 페이지 (2026-05-10 ingest). spec 결정의 backward
     evidence binding (LibreLane 3.0.2, MLPerf Tiny v1.3, §13 License
     Gate, KG-A~KG-E 등이 여기서 backing).

5. wiki/raw/imports_manifest.yaml
   → K1+K2 113 source의 decision_anchors · spec_contradictions ·
     critical_read 인덱스. 정찰용.

6. documentation:llm-wiki skill 5단계 ingest 워크플로 익히기
   → wiki/raw/{sessions,papers,blogs,repos,docs,benchmarks}/ 에 노트
     드롭 → wiki/{slug}.md 로 컴파일 → wiki/log.md 갱신 → 보조로
     make graph-update.

7. issues/README.md
   → 5개 open decision의 layer/gate 매핑. 자기 이슈 후보 식별.
```

### Developer 경로

```
1. make install / test / lint / fmt — 모두 통과 확인.

2. src/semi_design_runner/cli.py
   → semi-run / semi-metric-collector CLI entrypoint. pyproject.toml의
     [project.scripts] 와 함께 본다.

3. scripts/graph_integrity_check.py
   → L2.lint.check substrate. orphan=0 / dangling=0 / AMBIGUOUS≤0.3
     검사. NetworkX(`links`) + graphify-native(`edges`) 두 포맷 지원.

4. tests/
   → pytest. tmp_path + fixture 패턴. 절대 wiki/raw/ 실데이터를
     건드리지 않는다 (fixture graph만).

5. git log --oneline -20
   → commit 컨벤션 학습. docs(wiki) / docs(spec) / chore / feat / fix /
     test prefix. 한국어 본문 + English subject (imperative).

6. issues/README.md → 자기 이슈 후보 식별 (특히 L1/L2 코드 이슈).

7. CLAUDE.md (project) → AI 어시스턴트 협업 시 작업 규칙. 사람만
   작업하더라도 컨벤션·진입 우선순위가 다 적혀있어 유용.
```

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
/ `lint` / `sync` / `export` / `qmd-index` / `lancedb-sync`)을 사용한다.

## 6. 진입 지도 (Repository map)

| 경로 | 한 줄 |
|---|---|
| `README.md` | program overview + Knowledge base 정책 + Layer 분리. 첫 진입 정상화. |
| `CLAUDE.md` | AI 어시스턴트 협업 규칙. 사람도 컨벤션 reference로 유용. |
| `docs/glossary.md` | 용어집 (12살용 풀이 + 비유). 모르는 단어 즉시 조회. |
| `docs/onboarding.md` | **이 문서**. |
| `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` | **overview spec — single source of truth**. |
| `docs/superpowers/specs/2026-04-23-L2-substrate-design.md` | L2 substrate 파생 spec. |
| `docs/superpowers/plans/` | per-phase TDD 구현 plan. |
| `docs/knowledge-base/2026-04-19-k1-direction-report.md` | K1 종합 방향 판단. |
| `docs/learning/phase-0-curriculum.md` | Phase 0 마인드맵 + 진행 상태. |
| `wiki/index.md` | 위키 라우팅 hub (default 컨텍스트). |
| `wiki/{slug}.md` | 컴파일 페이지 (concept · policy · synthesis · decision · entity). |
| `wiki/raw/**` | 불변 seed corpus (sessions / papers / blogs / repos / docs / benchmarks). |
| `src/semi_design_runner/` | L1 Process Python CLI. wheel 진입점. |
| `scripts/graph_integrity_check.py` | L2.lint.check substrate. |
| `scripts/inject_freshness.py` | graphify 노드 freshness 주입. |
| `tests/` | pytest. tmp_path + fixture 패턴. |
| `issues/` | local 이슈 트래커 (5 open). 각 이슈 frontmatter는 layer/gate/blocks 명시. |
| `graphify-out/` | 보조 path 쿼리 산출물 (graph.json + GRAPH_REPORT.md + graph.html, Option A+ commit policy). |
| `Makefile` | 모든 표준 명령 정의. |
| `pyproject.toml` | uv 의존성 + ruff 설정 (100 char, py312) + script entrypoints. |

## 7. 작업 컨벤션 (요약)

- **Direct commits to `main`** — 현재 워크플로 (no feature branches).
- **Conventional commit prefix**: `docs(wiki)`, `docs(spec)`, `docs(glossary)`, `chore`, `feat`, `fix`, `test`. Subject는 imperative.
- **본문 한국어, slug/identifier는 English** — wiki page slug은 Obsidian `[[link]]` 호환을 위해 영어/하이픈.
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
| AI 어시스턴트 협업 규칙 | `CLAUDE.md` |
| spec ↔ source 의존성 (cross-component) | `make graph-serve` MCP 또는 `uv run graphify query "..."` |

## 9. 어디로 기여할 수 있는가 (Pending 영역)

| 영역 | 시작점 |
|---|---|
| **L1 파생 spec** (G1) | overview spec §6 + K2 ζ evidence + KG-A~KG-E |
| **L2 파생 spec 갱신** (G2) | `2026-04-23-L2-substrate-design.md` + K2 ε evidence (4 deferred items) |
| **L3 spec** (G3) | overview spec §13 License Gate 선행 + K2 θ evidence |
| **K2 ingest 결과 spec 갱신** | wiki K2 evidence 4 페이지 → overview spec §6.2 lockfile / §13 License Gate / §3.2 contracts 갱신 |
| **위키 새 페이지 컴파일** | wiki/index.md "Pending Compile" 섹션 (B branch HDL · KG-E DDB · Si2 Liberty · Cadence LEF/DEF · OpenSTA 등) |
| **graphify cross-link 정제** | `docs/graphify/cross-links.md` (bridge manifest), `make graph-lint` 통과 유지 |
| **이슈 해소** | `issues/{001~005}.md` 각 layer/gate 매핑 후 작업 |

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

이 둘을 섞으면 "wiki-first 정책이 agent 내부 API도 wiki로 바꾸자고 한다"는 잘못된 결론으로 이어진다. **wiki-first는 사람용, graphify는 agent 내부.** 두 결정은 독립이다.

---

> 더 깊이 들어가려면 `wiki/index.md` 의 "라우팅 규칙" 4단계와 `CLAUDE.md` 의
> "Before Non-Trivial Work" 5단계를 동시에 참조한다. 둘이 본 가이드의 압축
> 버전이다.
