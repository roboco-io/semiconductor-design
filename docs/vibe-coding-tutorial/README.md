# Vibe Coding Tutorial — 오픈소스 EDA + AWS + AutoResearch

> "AI를 활용해서 딥러닝 학습이나 추론에 사용할 반도체를 설계하고 싶어."
> — 2026-04-17 11:46, 첫 prompt

본 튜토리얼은 위 한 문장에서 시작해 11일간 107 commit으로 G1 통합 프로그램 직전까지 도달한 실제 Claude Code 세션 12개를 그대로 풀어쓴 기록이다. 각 chapter는 사용자가 실제로 입력한 prompt와 그 결과로 생성된 spec/code/decision을 함께 보여준다.

## 누구를 위한 튜토리얼인가

- **오픈소스 EDA 또는 AWS 인프라 엔지니어** — Yosys / OpenROAD / LibreLane을 Fargate Spot · Step Functions Map · DDB · S3 Object Lock 위에서 reproducible하게 굴리는 엔드투엔드 패턴 학습.
- **AI agent / vibe coding 관심자** — Claude Code SDK + Codex SDK 협업, AskUserQuestion · TaskCreate · run_in_background · superpowers skill 패턴, handoff를 통한 multi-session 컨텍스트 유지.
- **연구자** — Karpathy AutoResearch 스타일을 자신의 도메인에 적용. spec / decision-table / falsifier / publish-vs-kill rule 디자인 사례.

## 프로젝트 한 줄 요약

**"Report-Grounded Vibe-Coded AutoResearch for Open-Source DL Accelerator Design"** — Yosys + OpenROAD + LibreLane + sky130A를 SHA-pinned Nix bundle + AWS Fargate Spot 위에 올리고, LLM agent가 `synth.rpt` / `sta.rpt` / `drc.rpt`를 읽으면서 Gemmini 파생 미세구조를 탐색·검증하여 학술/프로세스 novelty를 도출하는 연구 프로그램. 절대 PPA보다 reasoning trace + reversible patch + report-grounded memory의 evidence를 우선시.

## 사전 지식

| 영역 | 필요한 깊이 |
|---|---|
| Python 3.12 + uv | `uv sync` / `pytest` 실행 가능 수준 |
| AWS | 계정 보유, IAM/S3/DynamoDB 개념 |
| TypeScript | `npm install` / `npx cdk synth` 실행 가능 수준 |
| 오픈소스 EDA | 처음이어도 무방 — chapter 01에서 학습 lens가 함께 정의됨 |
| Claude Code | 미사용자 OK. 본 튜토리얼이 SDK 명령을 항상 함께 보여줌 |

## 11일 타임라인 (2026-04-17 ~ 2026-04-27)

| 날짜 | 주요 마일스톤 | 주 chapter |
|---|---|---|
| 04-17 | 초기 prompt → brainstorming → archived spec → Phase 1a wiki → Phase 0 학습 시작 | 01 |
| 04-18 | Phase 0 A1/A2 (CMOS · 논리게이트) Q&A 세션 | 01 |
| 04-19 | EDA operator lens로 학습 retarget · K1 direction report 작성 시작 | 02 |
| 04-20 | K1 52 sources 적재 · integrated program overview 신설 (이전 spec archive) | 02 |
| 04-21 | L1 derived spec + plan + semi_design_runner Phase A 코드 (~30 commits) | 03, 06 |
| 04-22 | Phase 1a 폐기 → graphify 전환 (S1-S4) · K2 61 sources 추가 · LibreLane 3.0.2 / Fargate 200 GiB | 04 |
| 04-23 | L2 substrate spec + L2 schema + compute_confidence + inject_freshness + L2 regression | 05 |
| 04-23 | ComputeStack + WorkflowStack (B5/B6) + L1 LibreLane 2.4→3.0.2 sync | 06 |
| 04-26 | dry-run lockfile · L3 spec outline · l2_runtime real impl · ObservabilityStack · KG-A/D/E/F1 · metric-collector | 07 |
| 04-27 | lockfile real fill (Phase E1) · sample specs + run + CI (E2-E4) · 3 ORFS Dockerfile fix | 08 |
| (지연) | Phase E5+ AWS deploy · L1 G1 첫 실행 → `.rpt` 관찰 | 09 (debug 스토리만) |

## 비용·소요 시간

| 항목 | 값 | 비고 |
|---|---|---|
| 작업 시간 | ~80 시간 (11일 × 약 7시간) | 사람이 키보드 앞에 있던 시간 추정 |
| AWS 비용 | **$0.00** | Phase E5 (실 deploy) 미수행. CDK는 synth만 실행. ORFS/LibreLane Docker 빌드는 로컬 Mac에서만. |
| Claude Code 토큰 | 측정 안 함 | 12 세션, 최대 1M context · 평균 25-40% 사용. 약 5-15M 토큰 추정 |
| Codex 위임 | 4-5 회 | spec 3-round review · L1/L2 spec 검토 · 그 외 |
| 직접 commit (`main`) | 107 회 | branch 미사용 — direct main convention |

## 챕터 목차

### Part I — 기획 (G0)

**[Chapter 01 — 비전과 첫 pivot](01-vision-and-first-pivot.md)** · 4/17~4/19
- 초기 prompt와 D-목표(production-grade chip) 타협 → A-목표(MVP DSE)
- 5분 brainstorming + Codex 리뷰 + spec archive
- Phase 0 학습 시작 (CMOS / 논리게이트 / clock·timing / FSM)
- 4/19 핵심 pivot: "오픈소스 EDA + AutoResearch + 칩 아이디어 도출"

**[Chapter 02 — 지식 기반이 먼저](02-knowledge-first-direction.md)** · 4/19~4/20
- "spec·MVP 결정 전 최신 자료를 wiki에 ingest, 방향 판단은 그 이후" 원칙 도입
- K1 4축 52 sources (LLM-for-HDL · Agentic EDA · Open-source EDA · Research Memory)
- direction report 작성 → integrated program overview spec 생성, 4/17 spec archive
- Codex 3-round 리뷰 통과 패턴 정립

### Part II — L1 Process 구축 (G1 핵심 코드)

**[Chapter 03 — L1 spec과 코드의 동시 진화](03-l1-process-spec-and-code.md)** · 4/21
- L1 derived spec (Codex 3-round 통과)
- semi_design_runner 패키지: Pydantic schemas · lockfile · S3/DDB/SFN 클라이언트 · CLI
- `_StrictBase(ConfigDict(extra="forbid"))`로 layer-drift 방지
- L1 lockfile_sha의 cache contract: `_strip_nulls()` invariant

**[Chapter 04 — Phase 1a wiki를 폐기하고 graphify로](04-wiki-to-graphify.md)** · 4/22
- "knowledge plane을 spec/CLI 6+개 신설보다 외부 도구 1개 채택이 합리적"
- 4단계 Strangler 마이그레이션 (S1-S4): 평가 → ingest → 코드 swap → 잔재 제거
- graphify-out commit Option A+ 정책 (검색 인덱스를 git으로 관리)
- 76 orphan node를 cross-links.md (Path B bridge manifest)로 0화

**[Chapter 05 — L2 Substrate: 메모리·신뢰도·신선도·격리](05-l2-substrate.md)** · 4/23
- L2 derived spec (Codex 3-round 통과 · §3.3의 §5 confidence 격리 규칙)
- L2RecallNode Pydantic schema (9 optional 필드)
- compute_confidence (tier × source_count → GOLD/SILVER/BRONZE)
- inject_freshness (last_ingested · valid_from · valid_to A-MEM injection)
- 3-layer freeze (`__slots__` + `_FrozenMeta` + `MappingProxyType`) — runtime mutation 차단

**[Chapter 06 — CDK 6-stack composition](06-cdk-six-stack-composition.md)** · 4/21~4/26
- NetworkStack (9 VPC endpoints, NAT 없음) → StorageStack (S3 Object Lock + DDB×4 + KMS CMK)
- ContainerStack (3 ECR repos) → ComputeStack (Fargate TaskDefs · CMK ARN scoped)
- WorkflowStack (SFN Standard + Map(10) + 3 Lambdas + EventBridge)
- ObservabilityStack (CW dashboard + 3 alarms + $50/$100 budget)
- cdk-nag AwsSolutionsChecks + 4 Phase-E-deferred suppressions

### Part III — 통합 (G1 exit 직전)

**[Chapter 07 — Kill-gates와 L2 runtime의 실 구현](07-killgates-and-l2-runtime.md)** · 4/26
- dry-run lockfile.yaml hex-word convention (`deadbeef` / `cafebabe` / `feedface` / `yosys-N.NN-DRY-RUN`)
- L3 spec outline (§§1-2, 6-7 full draft, §§3-5 stub + 3 follow-up GitHub issue)
- l2_runtime.py 실 구현 (mock → real 전환 — 21 unit tests)
- KG-A / KG-D / KG-E / KG-F1 mandatory kill-gates + run-all aggregator
- metric-collector Docker 이미지 532 MB build 성공

**[Chapter 08 — Phase E1~E4: lockfile fill부터 CI까지](08-phase-e1-to-e4.md)** · 4/27
- AskUserQuestion으로 재개 경로 확정 → 4 upstream SHA 결정 (web 조회 + GitHub API rate-limit 우회)
- librelane_base 5번째 필드 발견 + `docker manifest inspect` multi-arch digest
- 4 sample specs (gcd-orfs · gcd-librelane · ibex-orfs · aes-orfs) + KG-F1 invariant
- `make run DESIGN=... STACK=... BUCKET=... STATE_MACHINE_ARN=...`
- `.github/workflows/ci.yml` 4 job (lint · test · cdk · graph)
- ORFS Dockerfile 3차 iteration (cmake 누락 → swig 4.0 vs 4.3 → DependencyInstaller switch)

### Part IV — 메타

**[Chapter 09 — 디버깅 스토리 모음](09-debugging-stories.md)**
- `tee` pipe가 exit code를 삼킨 ORFS 빌드 silent fail
- LibreLane Dockerfile의 `nix-build '<nixpkgs>' -A open_pdks` attribute 미존재
- Codex hand-pick apt list가 OpenROAD CMake findpackage version constraint를 따라잡지 못함
- Mac M-series 호스트에서 superclaude pytest plugin이 entry-point에 leak — `-p no:superclaude` workaround
- DDB의 `status`가 reserved word라 `ProjectionExpression="#s"` alias 필요

**[Appendix — Vibe coding toolkit](appendix-vibe-toolkit.md)**
- superpowers skills (brainstorming · writing-plans · subagent-driven-development · TDD · debugging)
- AskUserQuestion 글로벌 규칙 도입 (4/19 결정)
- handoff skill로 multi-session 컨텍스트 유지 (직접 작성한 글로벌 skill)
- Codex 3-round 독립 리뷰 패턴
- graphify로 wiki + AST 통합 지식 그래프

## Try It Yourself — 본 repo 따라하기

```bash
# 1. clone
git clone git@github.com:roboco-io/semiconductor-design.git
cd semiconductor-design

# 2. install (Python 3.12 + uv)
make install     # = uv sync --all-extras

# 3. fast tests (회귀 0)
uv run pytest -p no:superclaude -m "not slow" -v

# 4. CDK synth (AWS deploy 안 함)
cd cdk && npm install && npx cdk synth --context env=dev > /dev/null && cd ..

# 5. KG smoke gates (G1 mandatory)
make kg-all-smoke

# 6. graphify (지식 그래프 조회 — 본 튜토리얼의 anchor)
make graph-update           # AST-only incremental
uv run graphify query "lockfile cache contract"
```

## 메타데이터

- **last_generated**: 2026-05-01
- **last_log_message_uuid**: f9f24cdd-fbac-4500-bd9e-83ac741a9a2e (2026-05-01 11:10:14)
- **chapters**: 9 + appendix
- **total_commits**: 107 (`1ff20d6..01f6e79`)
- **target_audience**: 혼합 (EDA · AI agent · 연구자)
- **language**: 한국어 (기술 용어 영어 유지)
- **tutorial_status**: complete through G1 exit checklist; G4 (publish/kill 결정)는 Phase E5+ 실 AWS deploy 이후 추가 예정

## 라이선스

본 튜토리얼은 프로젝트 라이선스를 따른다. 프롬프트와 결과는 모두 실제 작업 기록이며 사후 가공을 최소화했다.
