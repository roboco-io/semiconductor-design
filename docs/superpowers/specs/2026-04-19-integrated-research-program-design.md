# Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator Design — Program Overview

| | |
|---|---|
| 작성일 | 2026-04-19 |
| 작성자 | Jung Do Hyun (serithemage@gmail.com) |
| 상태 | Draft — 통합 프로그램 방향 승인됨 (K1 증거 기반) |
| 전제 문서 | `docs/knowledge-base/2026-04-19-k1-direction-report.md`, `wiki/raw/papers/k1-*.md` (52 sources) |
| Supersedes | `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md` (archived) |
| Scope 구분 | **Program overview** — L1/L2/L3 sub-project 경계·인터페이스·novelty만 정의. 세부 설계는 각 layer 착수 직전 파생 spec 작성 |
| Reviews | Codex 1차 2026-04-20 (go-with-fixes, 10건) → 10 fix. 2차 2026-04-20 (needs-minor-revision, PARTIAL 2·new 5) → canonical table + §5.4 threshold summary + §8 G4 정렬 + 부록 C 4-sub-section + H1c direction. 3차 2026-04-20 (needs-minor-revision, PARTIAL 3·new drift) → §5.3 **precedence rule R0 + 완전성 확보(H1 × H3 6-row + override)**, §8 G4 §5.3 참조로 재단순화, §5.4 H1a threshold 강화(slope>0·α=0.05·R²≥0.3), H1b "최소 3건" source 반영, 부록 C 누락 knob 추가(scratchpad banking, target freq, memory pipeline, in-flight requests), C.4 모호함 제거(공식 문서화 parameter 기준) |

---

## 1. 프로젝트 의도 (재정의)

**AI를 활용해 반도체 설계 분야에서 도전적인 연구를 수행**한다. 구체적 연구 프로그램은 K1 지식 기반(52 sources, 4축)의 증거로부터 도출되었으며, 다음 세 seam이 4축에서 독립적으로 수렴한 결과다:

1. **Report-grounded agent operation** — `.rpt/.def/STA/DRC`를 structured memory로 취급
2. **Executable memory + template-breaking** — Voyager 스타일 reversible-patch skill library에 EDA transforms 축적, EvolVE 스타일 구조 아이디어 생성
3. **Process-as-contribution** — 수치가 아닌 reasoning trace + 재현성 번들이 학술 artifact

이 프로젝트의 최종 결과물은 **상용 대비 절대 PPA 우위가 아니라**, 다음 셋이며 각각 falsifier 조건이 동반된다(marketing phrase 아님):
- **Academic claim (논문)**: §4의 hypothesis H1/H2/H3 결과와 §5.4의 acceptance threshold, §5.3의 **canonical decision table**에 따라 publish / reframed-publish / kill을 결정한다. §1은 단일 기준을 단언하지 않고 §5.3 table을 참조한다.
- **Open-source reference**: 공개 repo clone 직후 unmodified 상태에서 `make run`이 gcd·ibex·aes 중 **최소 2개를 sign-off clean까지** 완주. CI에서 주기적 재검증(lockfile 고정, §6.2).
- **Process evidence**: 비전문가 평가자 **N≥5**가 reasoning trace 샘플을 읽고 "왜 후보가 채택/기각되었는가"를 정답과 Cohen's κ ≥ 0.6로 복원 가능해야 한다 (H3, §4.3). 평가자는 trace 생성 LLM과 **다른 LLM family** 이외에 인간 포함.

## 2. 비목표 (Not)

- 상용 EDA(Cadence/Synopsys/Siemens) 절대 PPA 대체
- 7nm 이하 공정 비교 (오픈 PDK는 130nm/180nm만 — 공정 대비는 원천 불가)
- 자체 LLM fine-tune (Claude Code SDK + Codex SDK만)
- Iter 1에서 실물 테이프아웃 (Efabless 셧다운으로 경로 자체가 불안정. 대체 경로 — ChipFoundry/wafer.space/IHP/Cadence shuttle — 는 Iter 3+ 검토)
- FireSim / FPGA 에뮬레이션 (Iter 2+)

## 3. 3-Layer 통합 구조

```
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 3 — CONTENT                                               │
 │   Open-Ideation DSE on Gemmini + MLPerf Tiny v1.3 streaming     │
 │   - 에이전트가 parameter vector가 아닌 "구조 idea" 제안         │
 │   - 각 idea는 reversible-patch로 표현, sign-off로 채택/기각    │
 │   - Scientific claim: ORFS-agent(2025) 대비 "다른 종류의 개선"  │
 │     (Pareto 수치 X, 실패 재사용률·새 구조 발견률 O)             │
 └─────────────────────────────────────────────────────────────────┘
                              ▲  reads/writes
                              │
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 2 — SUBSTRATE                                             │
 │   Report-grounded AutoResearch memory system                    │
 │   - `.rpt/.def/STA-slack/DRC` → typed-frontmatter 구조화 문서   │
 │   - Reversible-patch skill library (Voyager-style, EDA-native) │
 │   - `findings/`, `failures/`, `decisions/` 디렉토리 + QMD 검색층│
 │   - `wiki-lint`가 "이 실패는 finding X와 동일" 감지             │
 │   - 외부 노출 인터페이스: `skill-library.query()`, `memory.recall()`│
 └─────────────────────────────────────────────────────────────────┘
                              ▲  submits jobs / pulls artifacts
                              │
 ┌─────────────────────────────────────────────────────────────────┐
 │ Layer 1 — PROCESS                                               │
 │   SHA-pinned reproducibility bundle + AutoResearch harness      │
 │   - Nix bundle: LibreLane 2.4 + OpenROAD + Yosys + sky130A      │
 │     (+ gf180mcuD 옵션), 모두 SHA 디지스트 고정                    │
 │   - Local Python CLI orchestrator (uv) — Claude/Codex SDK 호출  │
 │   - AWS Fargate Spot + Step Functions Map (EDA burst 전용)       │
 │   - 인터페이스: `run(spec_uri) → artifact_uri`                   │
 └─────────────────────────────────────────────────────────────────┘
```

### 3.1 Layer 간 의존 관계

- L1 → L2·L3의 실행 substrate. L1이 최소 수준(smoke-test 통과)에 도달하기 전까지 L2·L3 실험 불가.
- L2와 L3는 서로 독립 개발 가능하나, L3의 "Open-Ideation" 품질은 L2의 skill library 성숙도에 비례.
- **sub-project 파생 spec은 각 layer 착수 직전 작성**. Overview 수준에서는 각 layer의 **인터페이스·성공 기준**까지만 고정.

### 3.2 Layer Interfaces — Contract Table (v2, 2026-04-22 graphify 전환, H3 대응)

> **Revision note (v2, 2026-04-22)**: Phase 1a wiki 엔진 기반 계약을 graphify v0.4.25 기반으로 재정의. 구현체·commit policy는 `docs/superpowers/specs/2026-04-22-graphify-adoption-design.md` §3.2·§4 참조. breaking 변경은 Codex 3-round 재승인 필요.

| Interface | Producer → Consumer | Input schema | Output schema | Immutability | Error taxonomy | Versioning | Min required fields |
|---|---|---|---|---|---|---|---|
| `L1.run(spec_uri)` | L1 orchestrator → L3 agents | `s3://…/spec.yaml` (Pydantic `Spec`, ULID `run_id`) | `s3://…/artifact/{run_id}/` bundle | Write-once, `_SUCCESS` marker 이후 immutable | `SpotReclaimed`, `OOM`, `TimingFail`, `DRCFail`, `ToolCrash`, `Unknown → DLQ` | `Spec.version: int` 필수, breaking 변경은 major bump | `run_id`, `status`, `metrics_uri`, `reports[]`, `cost_usd`, `provenance_uri` |
| `L2.skill_library.query(context)` | L2 substrate → L3 agents | `{name \| context}` (graphify `query "skill:<name>"` 또는 context 기반 lookup) | `[{skill_id, patch_uri, signed_off_report_uri, tier, last_verified}]` | `.claude/skills/`는 graphify 인덱싱 대상. 스킬 파일 자체는 git 관리, append-only per version; rename 금지; deprecation은 frontmatter `status` 필드로만 | `NoMatch`, `AmbiguousMatch`, `Uncached` (AMBIGUOUS skill 노드가 human review 대기 중일 때) | `skill.version: int` per-skill (skill frontmatter 필드) | `skill_id`, `patch_uri`, `attached_report_uri`, `last_verified`, `tier` |
| `L2.memory.recall(query)` | L2 substrate → L3 agents | `{query_text, k?, budget_tokens?}` (graphify BFS/DFS budget) | `[{node_id, label, source_file, tier, confidence_score, snippet?}]` | Read-only query over `graphify-out/graph.json`. 새 memory는 raw `.md` 파일로 write하고 `/graphify` rebuild 시 그래프에 반영 | `NoMatch`, `StaleGraph` (graph.json older than corpus), `AmbiguousTier` (AMBIGUOUS 비율 초과) | graph.json은 graphify version + corpus hash로 버전 식별 | `node_id`, `tier`, `confidence_score`, `source_file` |
| `L2.lint.check(graph_path)` | L2 substrate → CI / S3 (`make graph-lint`) | `graphify-out/graph.json` 경로 (default) 또는 명시적 path | `{ok: bool, errors: list[str], metrics: {orphan_count, dangling_count, ambiguous_ratio}}` | 임계선(orphan=0, dangling=0, AMBIGUOUS≤0.3)은 `scripts/graph_integrity_check.py`에 상수로 고정. 변경은 spec 재승인 | `OrphanNodeExists`, `DanglingEdgeExists`, `AmbiguousRatioExceeded`, `EmptyGraph` | integrity check 스크립트 version은 git SHA로 추적 | `ok`, `errors[]`, `metrics.orphan_count`, `metrics.dangling_count`, `metrics.ambiguous_ratio` |

**의미 gap 공지 (v2)**: graphify `tier`(EXTRACTED/INFERRED/AMBIGUOUS)는 **추출 신뢰도**이며 **주장 타당성**이 아니다. Phase 1a의 `confidence_score` frontmatter는 양자를 암묵적으로 포함했으나 v2에서는 명시적으로 분리. 소비자(L1/L3 agent)는 `tier`를 "검토 필요도" 신호로만 해석하고 **주장 타당성은 H1/H3 실험 결과(§5.3 canonical decision table)에서만 판정**한다.

**Contract 원칙**: 각 interface의 input/output은 Pydantic 스키마로 고정하고 `docs/superpowers/specs/2026-04-19-L{1,2,3}-*-design.md` 파생 시 그대로 상속한다. breaking 변경은 spec 재승인 필요.

### 3.3 각 Layer의 MVP 경계

| Layer | MVP 포함 | MVP 제외 |
|---|---|---|
| L1 Process | Nix bundle SHA-pin, Fargate Spot Map 10-conc, S3 artifact layout, DDB 4 테이블, 로컬 CLI orchestrator, 재시도 정책 | 실물 테이프아웃, FireSim, 다중 리전 |
| L2 Substrate | `.rpt/.def/STA` 파서, graphify v0.4.25 기반 graph index(`graphify-out/graph.json` + MCP serve), `scripts/graph_integrity_check.py` L2.lint, raw source는 `wiki/raw/**`·`docs/**` 유지, cross-trench bridge manifest | A-MEM 수준 memory evolution, Letta급 OS-paging, graphify의 자동 knowledge promotion(human review 경유) |
| L3 Content | gcd/ibex/aes 3개 디자인 대상 Open-Ideation 에이전트, MLPerf Tiny v1.3 KWS + streaming wakeword 평가, ORFS-agent와 대조 실험 | MLPerf Tiny 전체(IC/VWW/AD), Gemmini 외 가속기 템플릿 |

## 4. Novelty Hypotheses (K1은 plausibility만 지원, demonstrated novelty 아님)

> ⚠️ **중요**: K1 지식 기반(52 sources)의 frontmatter는 모두 `confidence: low`이며 β·δ 리포트는 해당 지점을 "open problem / novelty surface"로만 표현한다. 따라서 아래는 **실험으로 검증되어야 할 falsifiable hypotheses**이고, spec 작성 시점에는 demonstrated novelty가 아니다. 본 절은 H1/H2/H3의 주장과 falsifier를 함께 명시한다.

### 4.1 H1 — Primary Hypothesis (Report-grounded memory + reversible-patch library)

**주장**: 구조화된 리포트 메모리 + reversible-patch skill library를 갖춘 에이전트는 gcd·ibex·aes 3개 디자인에서 ORFS-agent(2025) 동일 compute budget 조건 대비 다음 H1a–H1c 중 **최소 2개**가 통계적으로 유의하게 개선된다 (independent seed × 3회 재현).

- **H1a — Finding reuse rate**: freeze된 duplicate-matching rule(§5.2-1)이 자동 매칭한 finding 비율이 iteration 반복에 따라 non-trivially 증가. blinded audit 통과 필수.
- **H1b — Non-knob structural patch**: 부록 C "Gemmini/Chipyard knob exclusion list"에 **없는** RTL/constraint transform이 sign-off를 통과한 건수. **최소 3건**, 각각 seed×3 재현 필수. exclusion list는 실험 개시 전 freeze.
- **H1c — Cold-start failure rate**: 새 디자인 첫 N=10 runs의 sign-off fail 비율. **방향: 낮을수록 좋음** — ORFS-agent baseline 대비 **감소**해야 pass.

**Falsifier**:
- H1a/H1b/H1c 중 2개 이상이 유의 개선을 못 보이거나,
- 개선이 있어도 §4.3 evaluator separation rule 위반·blinded audit 실패·exclusion list 사후 수정이 확인되면 H1은 기각.

### 4.2 H2 — Secondary Hypothesis (복리 효과)

**주장**: 동일 에이전트가 gcd → ibex → aes 순차 투입될 때 cold-start failure rate(H1c)가 **축적 findings 개수에 대해 음의 기울기**를 가진다. 통계 기준: linear regression slope, α=0.05.

**Falsifier**: slope가 0 또는 양수, 혹은 회귀 R² < 0.3.

### 4.3 H3 — Tertiary Hypothesis (process, reasoning-trace)

**주장**: Phase 0 curriculum을 완료한 비전문가 평가자 **N≥5**가 reasoning trace 샘플 K=20 이상을 읽고 "후보 채택/기각 이유"를 정답과 일치도 **Cohen's κ ≥ 0.6** 수준으로 복원할 수 있다.

**Evaluator separation rule (H5 대응)** — peer review에서 치명적이므로 명시적 규정:
- trace를 **생성**한 LLM과 trace를 **평가**하는 LLM은 **서로 다른 family** 여야 한다. Claude가 trace를 남기면 Codex가 평가하고 그 역도 성립. 인간 평가자가 추가 포함되지 않는 한, 같은 family의 self-scoring은 H3의 evidence로 인정하지 않는다.
- H3의 주 평가자는 **인간**이며, LLM 평가자는 보조 지표로만 사용.

**Trace failure-mode taxonomy (H5 대응)** — 다음 중 하나라도 해당하는 trace는 H3 score에서 자동 제외:
- **FM1. Hallucinated rationale**: trace의 도구 호출 흐름이 실제 실행 로그와 불일치
- **FM2. Post-hoc rationalization**: 결정 시점이 아닌 사후 재구성 흔적 (timestamp 불일치, 미래 정보 참조)
- **FM3. Omitted failed attempts**: 채택 경로만 서술하고 기각·실패 경로 누락 (원본 log 대비 diff로 검증)
- **FM4. Non-reproducible decision**: 동일 입력·동일 state에서 trace 재생성 시 다른 결정이 나옴

**Falsifier**: N < 5 모집 실패, 또는 집계 κ < 0.6, 또는 FM1~FM4 통과율이 50% 미만.

## 5. Evaluation Metrics (H7 재정렬: ORFS Pareto는 baseline only)

### 5.1 Layer별 지표

**L3 CONTENT — H1 novelty metrics (primary)**
- **H1a Finding reuse rate**: `L2.lint` duplicate-matching rule이 자동 매칭한 비율. rule은 실험 전 freeze (§5.2-1), blinded audit N≥2 통과 필수.
- **H1b Non-knob structural patch count**: 부록 C Gemmini-knob-exclusion-list에 없는 transform이 signed-off된 건수 × seed 재현성.
- **H1c Cold-start failure rate**: 새 디자인 첫 N=10 runs에서 sign-off fail 비율.
- **Baseline comparator (novelty 지표 아님)**: ORFS-agent(2025)와 동일 compute budget($) 하에서의 Pareto hypervolume — 보조 맥락 수치이며 H1의 acceptance 기준에 **포함되지 않음**. (Codex H7 반영: autotuning MVP가 novelty를 잃었으므로 Pareto는 baseline only)

**L2 SUBSTRATE — system metrics (보조, H1의 측정 도구)**
- Skill library reuse rate (Voyager 지표 차용)
- Negative-result recall accuracy — "과거 실패 조합을 다시 제안하는 비율" (낮을수록 좋음)
- Memory corpus drift (last_verified 분포)
- 이 지표들은 논문의 primary novelty claim으로 **직접 쓰이지 않으며**, H1 측정의 인프라 품질 증명용.

**L1 PROCESS — operational metrics**
- `make run` 재현성 (clean VM에서 pass rate)
- 세대당 비용 ($), 총 $30 이하 예산 준수
- Spot 회수 후 자동 복구 성공률, Kill-gate 통과 여부 (§8 KG-A~KG-E)

### 5.2 Measurement Safeguards (Codex C2 대응: gameable metric 방어)

1. **Freeze-before-experiment**: `L2.lint` duplicate-matching rule, H1b novelty patch 분류 규칙, blinded audit rubric을 실험 개시 전 **git tag로 freeze**. 중간 변경은 실험 무효 처리.
2. **Pre-registered Gemmini knob exclusion list (부록 C)**: `runtime-selectable dataflow (WS/OS/Both)`, `meshRows × meshCols`, `tileRows × tileCols`, `scratchpad size`, `inputType/accType`, `target freq`, Chipyard config options 등 기존 knob을 열거. 이 목록에 있는 것을 바꾸는 것은 **H1b "structural idea"로 카운트 금지**. 목록 수정은 실험 시작 전에만 가능하고, 이후 변경은 실험 무효.
3. **Blinded manual audit**: H1a·H1b의 자동 카운트는 운영자가 아닌 **독립 평가자 N≥2**가 blind로 샘플 검수. 일치율 <80%이면 자동 카운트 무효.
4. **Evaluator separation (H3)**: trace 생성 LLM과 평가 LLM은 서로 다른 family (§4.3).
5. **Pre-registration**: 실험 설계(sample size, acceptance threshold, exclusion list, seed seeds)를 OSF 또는 git tag로 pre-register. 사후 조정 금지.

### 5.3 Canonical Decision Table (Codex 2차·3차 지적 — §1/§5.3/§11 의미 통일 + 논리적 완전성)

본 table은 H1/H2/H3 결과로부터 publish / reframed-publish / kill을 결정하는 **유일한** 기준이다. §1 최종 결과물, §11 리스크 대응, §12 다음 단계, §8 G4는 모두 이 table을 참조하고 자체적으로 다른 기준을 선언하지 않는다.

**Precedence rule (override)**:
- **R0**: H3 evaluator separation 위반 OR H3 blinded audit 실패 OR FM1~FM4 pass율 < 50% OR 평가자 N < 5 → **kill**, 아래 모든 rule override. "평가 무결성 없으면 다른 결과는 무의미".

**R0 통과를 전제로** 다음 7행이 H1 pass 개수와 H3 validity 조합을 **완전히** 커버한다 (H1 ∈ {0, 1, ≥2} × H3 ∈ {pass, fail} = 6 + override row = 7):

| # | H1 pass 개수 (H1a/H1b/H1c 중) | H3 pass | 결정 |
|---|---|---|---|
| 1 | ≥2 | pass | **publish** (full primary) |
| 2 | ≥2 | fail | **reframed-publish** (H1 중심, process evidence 부재 노트 명시) |
| 3 | 1 | pass | **reframed-publish** (부분 H1 + process 결합) |
| 4 | 1 | fail | **kill** — primary도 tertiary도 약함 |
| 5 | 0 | pass | **reframed-publish** (process/tertiary 중심, H1 실패 원인 분석 포함) |
| 6 | 0 | fail | **kill** — 논문 claim 자체 성립 불가 |
| R0 | (any) | invalid | **kill** (override) |

**H2 보조 rule (R0/1-6 override 아님)**:
- H2는 **보조 신호**일 뿐 publish/reframed/kill 분기에 영향 없음.
- H2 pass: publish/reframed-publish의 강도 상승, 논문에 복리 효과 figure 포함.
- H2 fail: 논문에 "복리 효과는 본 실험에서 확인되지 않음" 명시.
- H2 미측정(디자인 순차 투입 전 중단 등): 논문에 "H2 범위 밖" 명시.

### 5.4 Acceptance Thresholds Summary (Codex 2차 지적 — §5.1 단독으로는 H2·H3 없음)

| Hypothesis | Threshold | 정의 위치 |
|---|---|---|
| H1a Finding reuse rate | freeze된 rule의 자동 매칭 비율이 iteration에 따라 **non-trivial하게 증가** (linear regression slope > 0, α=0.05, R² ≥ 0.3) + blinded audit N≥2 일치율 ≥80% | §4.1·§5.1·§5.2 |
| H1b Non-knob patch | 부록 C 제외 transform이 sign-off clean × seed×3 재현, 최소 3건 | §4.1·§5.1·부록 C |
| H1c Cold-start failure rate | ORFS-agent baseline 대비 **감소** (seed×3 평균) | §4.1·§5.1 |
| H2 복리 효과 | linear regression slope < 0, α=0.05, R² ≥ 0.3 | §4.2 |
| H3 Tertiary | N≥5 & Cohen's κ≥0.6 & FM1~FM4 pass율 ≥50% & evaluator separation 준수 | §4.3 |
| L1 process | `make run` clean-VM pass, 세대당 $ 추적, KG-A~KG-E 통과 | §5.1·§8 |

## 6. 아키텍처 (4-plane, 업데이트됨)

```
LOCAL plane (개발자 머신)
 └ Python CLI orchestrator (uv) — Claude Code SDK + Codex SDK
 └ SQLite population cache + .cache/traces/*.jsonl (LLM 원본 로그)
 └ semi-design-wiki 스킬 (wiki-init/sync/lint/ingest/query)

AWS plane (CDK TypeScript)
 └ Step Functions Standard Workflow — Map (maxConcurrency=10)
 └ Fargate Spot — rtl-build / synth / pnr / simulate / sign-off
 └ S3 artifact lake + DDB 4 tables + ECR 4+ repos + EventBridge
 └ (Iter 2 option) CloudFront + 정적 대시보드

TOOL plane (SHA-pinned)
 └ LibreLane 2.4 (FOSSi Foundation) + OpenROAD + Yosys + Verilator + cocotb
 └ open_pdks sky130A (+ gf180mcuD optional)
 └ Chipyard 1.13 + Gemmini (main@SHA) + mlcommons/tiny v1.3

KNOWLEDGE plane (git-backed)
 └ wiki/ (Phase 1a engine + Phase 1b ingest)
 └ wiki/raw/{papers,docs,repos,benchmarks,blogs,sessions}/
 └ findings/ failures/ decisions/ (신규)
 └ program/program.md + scoring.md + promotion_policy.md (신규)
 └ QMD corpus + index (hybrid search 제공)
```

### 6.2 Reproducibility Lockfile (Codex M8 대응)

SHA pinning 이상으로 재현성을 못박기 위한 단일 lockfile 의무화.

- **파일 위치**: 리포 루트 `lockfile.yaml`
- **필수 필드**:
  - `commit_shas`: OpenROAD, LibreLane, Yosys, Verilator, cocotb, Chipyard, Gemmini, mlcommons/tiny 등 모든 upstream repo의 사용 SHA (K1에서 "Gemmini는 `main` only 태그 없음", "OpenROAD 릴리스 태그 fetch 실패" caveat 반영).
  - `container_digests`: ECR 이미지별 SHA256 digest 매핑
  - `source_tarball_mirrors`: 각 upstream의 S3 미러 경로 (upstream 저장소 소멸·이관 대비 — Efabless 사례)
  - `stale_source_policy`: 미러 fetch 실패 시 24h grace period, 이후 CI 레드로 전환
  - `pdk_digests`: open_pdks (sky130A + 선택 gf180mcuD) 고정 버전
- **업데이트 규칙**: `lockfile.yaml` 변경은 별도 PR. master 병합 시 CI가 전체 재빌드 성공 증명 필요. Iter 내에서는 SHA 불변, 업데이트는 Iter 경계에서만.
- **검증**: `make lockfile-verify`가 `make run` 이전에 자동 실행.

### 6.3 기존 스펙 대비 변경점

| 항목 | 기존 (2026-04-17) | 현재 (2026-04-19) |
|---|---|---|
| 대상 문제 | Gemmini DL 가속기 end-to-end 설계 | L3 Content로 **보존**되며, **Open-Ideation + report-grounded**로 확장 |
| EDA 스택 | `efabless/openlane2@main` (Nix) | **LibreLane 2.4** (FOSSi Foundation) — 이름·오너십 변경 반영 |
| 벤치마크 | MLPerf Tiny v1.2 (KWS 단일) | **v1.3** (streaming wakeword 포함) |
| Iter 3 계획 | Efabless Shuttle 테이프아웃 | **삭제** (Efabless 2025-02 셧다운). 대체 경로 검토는 Iter 3+ |
| 지식 계층 | `wiki/` + 수동 ingest | `wiki/` + **QMD + findings/failures/decisions/ + program.md** |
| 에이전트 | 8종(Spec/Architect/RTL/TB/Verif/Signoff/Evaluator/Planner) | 3층 구조 내부에서 재편. RTL/TB는 L3에 종속. Reader/Synthesizer는 L2에 종속. 구체 종수는 파생 spec에서 확정 |
| Autotuning-only MVP | (하이브리드 안으로 제안됨) | **폐기** — ORFS-agent(2025) 존재로 novelty 소실 |

## 7. 운영 원칙 (program.md 초안)

작성될 `wiki/program/program.md`에 포함될 최상위 규칙:

1. **작은 reversible patch만 허용.** baseline 덮어쓰기 금지. promotion gate 통과 후에만 baseline 승격.
2. **모든 claim은 evidence로 지탱.** wiki 페이지는 `confidence, contradiction, last_verified` 필드 필수.
3. **Negative result도 자산.** `failures/`에 축적. 삭제 금지.
4. **감독은 운영자 책임.** 에이전트 자동 결정은 log되지만 promotion은 운영자 승인 필요.
5. **Process > 수치.** 논문 claim의 일부는 reasoning trace 자체다. PPA 수치가 나오지 않아도 프로그램은 진행.

## 8. 실행 순서 (게이트 기반, 주단위 없음)

### G0 — Program bootstrap (현재 진행중)
- ✅ K1 지식 수집 (52 sources)
- ✅ Program overview spec (이 문서)
- ⏳ 기존 spec archive + 참조 문서 갱신 (README/CLAUDE/issues)
- ⏳ L1/L2/L3 sub-project 파생 spec 착수 순서 합의

### G1 — L1 Process bootstrap (with explicit kill gates, Codex H4 대응)
- L1 파생 spec → writing-plans → 구현 → `make run` gcd 한 줄 재현 성공
- **Kill gates (각 fail 시 L1 재설계 강제, L2/L3 진입 불가)**:
  - **KG-A (LibreLane on Fargate)**: LibreLane 2.4 Nix 이미지가 Fargate Spot 4vCPU 16GB에서 gcd flow를 timeout(30분) 내 완주. 실패 시 8vCPU/32GB 또는 OpenROAD-only fallback 검토.
  - **KG-B (Chipyard+Gemmini build)**: Chipyard + Gemmini 빌드가 Fargate Spot에서 성공. 메모리 16GB 한도 초과 시 S3 prebuilt cache 또는 사전 빌드 baseline artifact로 우회.
  - **KG-C (LLM SDK quota)**: Claude SDK + Codex SDK가 "10-후보 세대 × 하루 1세대 × 7일"의 호출 패턴에서 rate limit을 견딤. 초과 시 세대 일시 중단 + retry 스케줄링.
  - **KG-D (Spot reclaim tolerance)**: PnR >20분 job이 Spot pre-emption 후 최대 2회 재시도로 완주율 ≥ 80%. 미달 시 on-demand fallback 혼합.
  - **KG-E (DDB write amplification)**: candidate 1개당 DDB PutItem < 50회. 초과 시 Candidates 테이블 schema 단순화 또는 Events 테이블 TTL 단축.

### G2 — L2 Substrate bootstrap (L1 완료 후 병렬 시작)
- L2 파생 spec → writing-plans → `.rpt` parser + typed-frontmatter 생성기 + QMD 인덱스 구축
- 게이트: 동일 failure 2회 투입 시 lint가 duplicate finding으로 자동 매칭

### G3 — L3 Content MVP (L1 완료 + L2 부분 완료 후)
- L3 파생 spec → writing-plans → Open-Ideation 에이전트 + MLPerf Tiny v1.3 harness
- 게이트: gcd·ibex·aes 3개 디자인에서 베이스라인 대비 "다른 종류의 개선" 최소 1건 관측

### G4 — 통합 실험 + 논문 figure
- 복리 효과 축적 실험 (디자인 순차 투입), reasoning trace 샘플 수집, ORFS-agent 대조 런
- 게이트: **§5.3 Canonical Decision Table의 `publish` 또는 `reframed-publish` 경로 중 하나 충족**. G4는 자체 기준을 선언하지 않고 §5.3만 참조한다. (§5.3 행 1·2·3·5가 모두 `publish` 또는 `reframed-publish` — 행 4·6·R0는 kill이므로 G4 통과 불가)

**주 단위 일정은 설정하지 않는다.** 각 게이트 통과 시점에 다음 게이트의 태스크·의존성을 산정. 독립 태스크는 병렬 실행.

## 9. 기존 Spec 폐기 항목 (즉시 무효)

- Iter 3 Efabless Shuttle 테이프아웃 계획
- `efabless/openlane2@main` 스택 참조
- MLPerf Tiny v1.2 기준 벤치마크 목표
- 8-에이전트 8주 MVP 일정 (주단위 W1-W8)

## 10. 기존 issues/ 재배치 (예비)

| ID | 제목 | 재배치 후 status / layer |
|---|---|---|
| 001 | Planner crossover 알고리즘 | L3 파생 spec 범위 — 단순 crossover가 아니라 **structural mutation operator 설계**로 재정의 |
| 002 | Fargate Spot vs On-Demand 혼합 | L1 파생 spec — Spot 확정 후 retry 정책 문서화로 축소 |
| 003 | Wiki ingest 자동화 | L2 파생 spec — QMD 도입과 통합, M1~M3 단계적 |
| 004 | 대시보드 프레임워크 | L1 관측성 또는 L3 모니터링으로 분할 가능. Iter 1 MVP 내 도입 여부는 L1 파생 spec에서 결정 |

개별 이슈 파일 본문 업데이트는 후속 턴에서 수행.

## 11. 리스크 · 대응 (Codex H4·M9 반영)

| 리스크 | 대응 |
|---|---|
| H1 전체 실패 (ORFS-agent 대비 차별화 측정 안 됨) | **§5.3 Canonical Decision Table에 따라 결정.** 자체 판단 금지 — §11이 §5.3과 다른 결정 기준을 선언하지 않는다 |
| LibreLane 2.4 Nix가 Fargate에서 미가동 | KG-A에서 조기 검증. 실패 시 OpenROAD 단독 + 수동 스크립트로 다운그레이드 (LibreLane 제거, 성능 penalty 문서화) |
| **Chipyard + Gemmini 빌드 Fargate 메모리 초과** | KG-B. S3 prebuilt cache, 또는 Chipyard 사전 빌드 baseline artifact. 8vCPU/32GB fallback 혼합 |
| **Claude/Codex SDK quota/rate limit** | KG-C. 세대 시작 전 rate-limit dry-run, 초과 시 세대 일시 중단 + exponential backoff. Codex 접근성 문제 시 Claude로 일원화(novelty에 타격은 있음) |
| **긴 PnR(>20분) 중 Spot reclaim** | KG-D. Pre-emption signal 감지 후 checkpoint 저장, 다음 task에서 resume. 재시도 실패 시 on-demand fallback |
| **DDB 4테이블 write amplification** | KG-E. candidate당 PutItem 상한 모니터링 + 초과 시 Candidates schema 단순화, Events TTL 단축 |
| Gemmini `main` SHA가 fast-moving | `lockfile.yaml`에 SHA 고정 (§6.2). 업데이트는 Iter 경계에서만 |
| L2 substrate 구현 난도 (typed frontmatter + QMD + lint 확장) | MVP scope를 `.rpt` parser + duplicate-failure lint rule 2개로 최소화. A-MEM급 memory evolution은 배제 |
| **Evaluator circularity (H3)** | §4.3 evaluator separation rule 강제. 인간 평가자 N≥5 확보 실패 시 H3 자체가 invalid — no-go 트리거 |
| **Aspirational metrics의 gameability** | §5.2 safeguard 5종(freeze-before-exp, exclusion list, blinded audit, pre-registration, separation) — 모두 위반 시 해당 실험 회차 무효 |
| **Academic invalidity (project-killing)** | **§5.3 Canonical Decision Table 참조.** kill 조건 충족 시 프로젝트 의도 재수립 또는 종료. reframed-publish 경로는 table의 해당 행 존재 시에만 허용 |
| **License/provenance (NVDLA 등)** | **§13 License & Provenance Gate** 통과 전까지 NVDLA 사용 금지. Gemmini(BSD 3-clause) 우선 |
| Efabless 대체 경로 불확실 | Iter 1은 sign-off 시뮬레이션까지만. 실물 테이프아웃은 Iter 3+ ChipFoundry/wafer.space/IHP/Cadence shuttle 중 선택 |

## 12. 다음 단계

1. **이 overview spec을 사용자가 리뷰 → 승인 또는 수정 지시**
2. 승인 시:
   - 기존 spec archive mark (완료 ✅ 2026-04-19)
   - README.md / CLAUDE.md / issues/ 4건 업데이트
   - **License & Provenance Gate (§13) 1차 준비** — license matrix 초안 + corpus-separation 규칙
   - `writing-plans` 스킬로 **L1 파생 spec 또는 plan** 작성 착수 (L1이 선행)
3. L1 plan 작성 중 L2·L3 파생 spec 병렬 착수 가능 (L1에 의존하지 않는 부분)

## 13. License & Provenance Gate (Codex H6 대응, L3 착수 전 통과 필수)

L3 Content는 외부 IP·license가 가장 민감한 layer다. 핸드오프 문서 §5·§16이 요구한 provenance·권한 분리를 여기서 제도화한다.

- **Source license matrix** (`docs/provenance/license-matrix.md`): 사용 upstream마다 license, 유효 버전·SHA, 상용 재배포 가능 여부, 결과물 파생권 제약을 매트릭스로 유지.
- **NVDLA-specific**: NVIDIA Open NVDLA License와 본 프로젝트 공개 artifact 번들의 호환성을 **법률 검토 또는 공신력 있는 선례 조사 전까지** L3 scope에서 제외. Gemmini(BSD 3-clause)가 우선.
- **Artifact lineage**: 모든 L3 출력 artifact(`rtl/`, `tb/`, `synth/`, `pnr/`, `signoff/`)는 동반 `provenance.yaml`에 source origin + transform chain + agent ID + LLM family/버전 기록.
- **Public/private corpus separation**: `wiki/raw/private/` 경로는 `wiki-lint`가 public export 차단. 고객 IP·비공개 PDK·non-public datasheet는 `private/`에만 허용. private → public 이관은 별도 승인 워크플로우 필요.
- **Gate 통과 기준**: license-matrix와 corpus-separation test가 CI 그린, NVDLA 검토 완료 또는 exclusion 확정, 모든 L3 artifact 샘플이 `provenance.yaml`을 동반.

## 부록 A — 참조

- K1 방향 판단 리포트: `docs/knowledge-base/2026-04-19-k1-direction-report.md`
- 축별 자료: `wiki/raw/papers/k1-{alpha,beta,gamma,delta}-*.md`
- 자료 인덱스: `wiki/raw/imports_manifest.yaml`
- Superseded: `docs/superpowers/specs/2026-04-17-semiconductor-design-agent-design.md`
- Phase 0 학습 상태: `docs/learning/phase-0-curriculum.md` (EDA 운영자 렌즈 유지 — 본 프로그램의 "비전문가 운영자" 조건과 직결)
- EDA 에이전트 핸드오프 노트: `docs/eda_agent_handoff.md` (ORFS autotuning 단독 MVP 가정은 무효화)

## 부록 B — Codex 리뷰 반영 추적

| # | Severity | Codex 지적 요지 | 반영 위치 |
|---|---|---|---|
| C1 | critical | Primary claim → hypothesis로 | §4 전체 (H1/H2/H3 재구성) |
| C2 | critical | Gameable metrics (finding reuse, structural idea) | §5.2 safeguards + 부록 C (3차에서 H1a threshold 강화·부록 C 누락 knob 보강·C.4 공식문서 기준으로 모호함 제거 완료) |
| H3 | high | L1/L2/L3 interface contract 부족 | §3.2 contract table |
| H4 | high | Hidden landmines 누락 | §8 G1 KG-A~KG-E + §11 risk 보강 |
| H5 | high | Evaluator circularity | §4.3 separation rule + trace failure-mode taxonomy (FM1~FM4) |
| H6 | high | IP/license/provenance 약함 | §13 License & Provenance Gate |
| H7 | high | "Autotuning 폐기" vs "ORFS Pareto 비교" 모순 | §5.1에서 ORFS Pareto를 baseline-only로 강등 |
| M8 | medium | Reproducibility lockfile 부재 | §6.2 lockfile.yaml 의무화 |
| M9 | medium | No-go condition 부재 | §5.3 + §11 academic invalidity 행 |
| M10 | medium | Marketing phrase 교체 | §1 each bullet에 falsifier + threshold 포함 |

## 부록 C — Gemmini/Chipyard Knob Exclusion List (H1b "non-knob structural idea" 판정용, freeze 대상)

다음 항목의 변경은 **기존 knob 조작**이며 H1b "structural idea"로 카운트하지 않는다. 이 목록은 실험 개시 전 git tag로 freeze하고, 이후 변경은 실험 무효 처리. Codex 2차 지적을 반영해 Gemmini config + Chipyard config + 주변 시스템 knob을 모두 열거한다.

### C.1 Gemmini systolic array config
- Dataflow: `WS`, `OS`, `Both` (runtime-selectable)
- `meshRows × meshCols`, `tileRows × tileCols`
- `inputType` (SInt 비트폭), `accType`/`accumulatorType` (SInt 비트폭)
- PE latency/pipeline stage count (기존 Gemmini config에 노출된 것)
- Target clock/frequency constraint (SDC `create_clock`, ORFS `CLOCK_PERIOD`, Chipyard freq option 등 기존 flow에 노출된 모든 frequency knob)

### C.2 Memory hierarchy / banking
- `scratchpadSize` (KB), scratchpad **포트 수**, scratchpad **banking factor** (bank 분할 방식도 포함)
- Accumulator size, accumulator **banking factor**
- Gemmini memory pipeline depth, max in-flight memory requests / outstanding loads
- L1/L2 cache sizes, line size, associativity, replacement policy (Chipyard config class 변경)
- TLB entries, TLB replacement policy
- DMA engine width, DMA buffer depth, DMA queue depth
- Bus width (TileLink/RoCC interface), bus channel count

### C.3 Microarchitecture queue / pipeline sizing
- ROB size, LSQ size, issue width, dispatch width
- BOOM 파이프라인 stage depth, Rocket pipeline depth
- Branch predictor size/type (기존 제공된 변형)
- Gemmini command queue depth, ld/ex/st queue depth

### C.4 Flow / simulation knobs (모호 표현 제거 — Codex 3차 지적)
이 sub-section은 **upstream tool의 공식 문서(README/manual/CLI --help 출력)에 문서화된 parameter 전체**를 대상으로 한다. "tool에 노출된 것"처럼 모호한 표현은 사용하지 않으며, 각 항목은 specific tool + specific parameter 이름으로 특정된다.

- **Chipyard**: `config/` 디렉토리의 모든 `Config*` fragment 포함/제외, `build.sbt` 공식 options
- **Verilator**: 공식 manual(verilator --help)에 문서화된 모든 flag. 시뮬 cycle budget, `--trace`·`--trace-depth`, `--threads`, optimization flags
- **cocotb**: 공식 docs에 문서화된 fixture/fixtures 옵션
- **Yosys**: `synth`·`synth_*` command의 공식 flag, `read_verilog`·`write_verilog` 표준 옵션
- **OpenROAD / ORFS**: `config.mk` 파일과 ORFS 공식 docs에 명시된 모든 변수 — `CORE_UTILIZATION`, `PLACE_DENSITY`, `GLOBAL_ROUTING_ITERATIONS`, `TIMING_DRIVEN`, `CTS_CLUSTER_SIZE`, `MACRO_PLACE_HALO`, `DFF_*` 등 전부
- **LibreLane 2.4**: 공식 config schema에 정의된 모든 step parameter
- **SDC constraints**: `create_clock`, `set_input_delay`, `set_output_delay`, `set_clock_uncertainty`, `set_max_delay`, `set_driving_cell`, `set_load` 등 표준 SDC command의 파라미터

**판정 기준**: 특정 patch가 "knob 변경"인지 "non-knob structural"인지 애매할 때 — 해당 upstream tool의 공식 문서에 해당 parameter가 언급되어 있으면 knob으로 간주. 공식 문서에 없는 transform(예: RTL 모듈 추가/재구성, 새 command/step 정의, upstream에 없는 constraint pattern)만 H1b로 카운트.

**업계 관행 quality note**: H1b 후보는 "upstream(Gemmini/Chipyard/OpenROAD) issue/PR로 제출 가능한 형태"면 더 강한 증거가 되지만, 이는 novelty 판정 기준이 아니라 **quality signal**일 뿐이다. H1b 카운트는 위의 "knob 여부" 판정만으로 충분.

**H1b로 카운트되려면**: 위 C.1~C.4의 어디에도 없는 RTL·constraint·flow transform이어야 하며, 다음 **3가지를 모두 충족**:
1. sign-off clean 통과 (DRC/LVS/STA 모두)
2. blinded audit(N≥2) 승인 — "이것이 기존 knob 변경이 아니다"
3. seed×3 재현

Exclusion list에 빠진 knob이 발견되면 **실험 개시 전에만** list에 추가 가능. 실험 시작 이후 list 변경은 해당 회차 실험 무효.
