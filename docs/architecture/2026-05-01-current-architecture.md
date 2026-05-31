# 현 시점 아키텍처 스냅샷 — 2026-05-01

| | |
|---|---|
| 작성일 | 2026-05-01 |
| 종류 | **As-built snapshot** (시점 사진. 영구 spec 아님) |
| 권위 spec | `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` |
| 보완 관계 | spec은 의도/계약, 본 문서는 "지금 실제로 돌아가는 게 무엇인가" |
| 다음 사본 | 의미있는 표면 변화가 생기면 새 날짜 prefix 파일로 추가 (이 파일은 그대로 둠) |

본 문서는 spec의 3-layer 구조를 다시 정의하지 않는다. 대신 **2026-05-01 기준 repo의 코드·CDK·Docker·graphify 표면이 무엇인지**, **spec 의도와 비교해 어디까지 와 있는지**를 한 장으로 보여준다.

---

## 1. 한눈에 — 3-Layer × 구현 매트릭스

| Layer | spec 의도 | 2026-05-01 구현 표면 | 상태 |
|---|---|---|---|
| **L1 Process** | SHA-pinned Nix 번들 + AWS Fargate Spot + SFN Standard | `src/semi_design_runner/` (CLI + AWS wrappers + lockfile) · `cdk/` (6-stack) · `docker/` (3 Dockerfile + 3 build script) · `lockfile.yaml` (4 SHA 채워짐, container_digests `librelane_base` 1건 채움) | **거의 완성** — ORFS docker build 미실행, KG-A~F1 일부 통과 |
| **L2 Substrate** | typed-frontmatter memory + skill library + lint + recall | `src/semi_design_runner/{l2_runtime,l2_schema,confidence}.py` · `scripts/graph_integrity_check.py` · `graphify-out/` (graphify v0.4.25 게이트웨이) | **부분** — `lint.check`/`memory.recall` 골격, `skill_library.query` 미구현 |
| **L3 Content** | Open-Ideation DSE on Gemmini + MLPerf Tiny v1.3 | (없음) | **미착수** — License Gate (spec §13) 선행 |

> spec §3.2 contract table의 4 인터페이스 중 `L1.run`·`L2.lint.check`·`L2.memory.recall`은 호출 가능, `L2.skill_library.query`는 미구현.

---

## 2. 코드 표면 (실제 import 가능한 것들)

### 2.1 Runner CLI — `src/semi_design_runner/`

```
semi-run init             specs/*.yaml → S3 + DDB Candidates 1행 (gen=0 cand=0)
semi-run lockfile-verify  --scope l1: 4개 SHA + 1개 digest 모양 검사 + l1_lockfile_sha 출력
semi-run auth login       AWS SSO 로그인 (profile: semi-design-operator)
semi-run submit           run_id로 SFN execution 시작 → execution_arn 반환
semi-run status           DDB.Candidates.status × SFN.describe_execution.status JSON 조인
semi-run artifacts        s3://{bucket}/runs/{run_id}/ → 로컬 dest 동기화
semi-run cost             DDB.Runs.total_cost_usd (budget guard와 같은 값)
semi-metric-collector     Fargate task entrypoint (별도 콘솔 wheel)
semi-confidence           graphify graph confidence 도구 (L2 보조)
```

기본 테이블/버킷은 `--env`로 결정 (`semi-design-{env}-Candidates|Runs`, `semi-design-{account}-{region}`). 환경변수 `SEMI_DESIGN_ENV`/`SEMI_DESIGN_BUCKET`으로 override.

내부 모듈:
- `aws/{clients,s3,ddb,sfn}.py` — boto3 thin wrappers (테스트 가능한 단일 책임 분리)
- `lockfile.py` — `_strip_nulls` 적용 후 canonical YAML SHA-256 → `l1_lockfile_sha` (캐시 키)
- `schemas.py` / `validator.py` — Spec pydantic + G1-scope 거부 (`RejectedNotInG1Scope`)
- `metrics.py` / `cost.py` / `trace.py` — 지표·비용·trace 수집
- `l2_runtime.py` (`L2Runtime` `_FrozenMeta` immutable singleton) + `l2_schema.py` (`L2RecallNode`) + `confidence.py` — L2 recall/confidence 골격

### 2.2 CDK 6-Stack — `cdk/`

`cdk/bin/semi-design.ts`의 `buildApp()`은 다음 순서로 합성한다 (괄호 안은 cross-stack 의존):

```
NetworkStack          VPC(2 AZ, NAT 1개, S3 endpoint)
   ↓ vpc
StorageStack          S3 artifact bucket(CMK) · DDB 3 tables(Candidates/Runs/Events)
   ↓ bucketCmk, tables
ContainerStack        ECR 3 repos (orfs-runner / librelane-runner / metric-collector)
   ↓ repos
ComputeStack          ECS Cluster (Fargate Spot capacity providers, ContainerInsightsV2)
                      + 3 TaskDef (taskRole는 s3:Get/Put runs/* + kms:Decrypt explicit ARN)
   ↓ cluster, taskDefs, bucket, tables
WorkflowStack         SFN Standard
                      validate → initGen → Map(maxConcurrency=10).itemProcessor(candidateChain)
   ↓ tables
ObservabilityStack    AWS Budgets(project tag filter) · 향후 alarm/log group
```

전 스택에 root `Aspects.add(AwsSolutionsChecks)` (cdk-nag) — Network/Storage/Compute/Workflow는 spec §16.3 사유 명시 suppression 적용. 모든 스택에 `Tag project = semi-design-{env}`.

### 2.3 Docker Runners — `docker/`

| Runner | Dockerfile | 빌드 인자 (lockfile에서 주입) | 진입점 |
|---|---|---|---|
| ORFS | `orfs-runner.Dockerfile` | `OPENROAD_SHA`, `YOSYS_TAG`, `OPEN_PDKS_SHA` | `entrypoints/orfs-run.sh` |
| LibreLane | `librelane-runner.Dockerfile` | `LIBRELANE_DIGEST`, `LIBRELANE_REF`, `OPEN_PDKS_SHA` | `entrypoints/librelane-run.sh` |
| Metric collector | `metric-collector.Dockerfile` | (wheel만) | `semi-metric-collector` |

빌드 스크립트 `build-{orfs,librelane,metric-collector}.sh`는 `--push` 분기 안에서만 `ECR_REGISTRY`를 요구 (로컬 빌드 unblock). Docker 통합 테스트(`tests/docker/test_*_runner.py`)는 `lockfile.yaml`을 `yaml.safe_load`로 읽어 build args를 주입한다.

### 2.4 Knowledge Substrate — `graphify-out/`

```
graphify-out/
├── graph.json          AST + ingest 산출 (commit 대상 — Option A+ policy)
├── GRAPH_REPORT.md     God nodes · communities · suggested questions
├── graph.html          시각화
├── manifest.json       ingest 메타
├── memory/             query/path/explain 결과 캐시 → 다음 update 시 재인제스트
└── cache/              gitignored
```

운영 통로:
- `make graph-update` — AST-only 증분 (빠름)
- `make graph-build` — 안내만; 풀 리빌드는 `/graphify .` AI 세션에서
- `make graph-serve` — graphify MCP 서버 (`L2.memory.recall` 공급)
- `make graph-lint` → `scripts/graph_integrity_check.py` (orphan=0 / dangling=0 / AMBIGUOUS≤0.3)
- `uv run graphify query "..."` — ad-hoc BFS
- `uv run graphify explain "<node>"` — 단일 노드 plain-language 설명

`.mcp.json`에서 graphify를 MCP 서버로 등록, `.claude/settings.json`의 `UserPromptSubmit` 훅이 `scripts/graphify_auto_context.py`로 사용자 프롬프트별 subgraph를 자동 주입한다.

---

## 3. End-to-End 데이터 흐름 (operator view)

```
operator
   │  semi-run init --spec specs/gcd.yaml --env dev
   ├─► validator.validate_spec_for_g1()        (G1 scope 위반 시 거부)
   ├─► s3.put_spec()                           s3://semi-design-{acct}-{region}/specs/{run_id}.yaml
   └─► ddb.put_candidate_with_count()          Candidates: gen#0#cand#0, status="initialized"

operator
   │  semi-run submit --run-id ... --state-machine-arn ...
   └─► sfn.start_execution()                   → execution_arn

Step Functions (Standard)
   validate ─► initGen ─► Map(maxConcurrency=10)
                          └─ candidateChain (per cand)
                              ├─ orfs-runner / librelane-runner Fargate Spot task
                              │     stdout → CloudWatch Logs
                              │     artifacts → s3://.../runs/{run_id}/{gen}/{cand}/
                              ├─ metric-collector task
                              │     parses .rpt → Candidates.{stage_status, metrics}
                              └─ DDB Events append

operator
   │  semi-run status --run-id ... --execution-arn ...
   ├─► ddb.get_item(Candidates, gen#0#cand#0, ProjectionExpression="#s")
   │       └─ status는 DDB 예약어라 #s alias 강제
   └─► sfn.describe_execution() → JSON 조인 출력

operator
   │  semi-run cost --run-id ...    → Runs.total_cost_usd (budget guard와 동일 source)
   └─  semi-run artifacts ...       → s3 sync runs/{run_id}/ → 로컬
```

---

## 4. spec 의도와의 gap (현 시점)

spec에서 정의했지만 아직 비어 있는 부분 — 본 스냅샷의 의의는 이 gap을 명시적으로 노출하는 것.

| 영역 | spec 위치 | 현 상태 |
|---|---|---|
| **L1 KG-B/C** kill-gate (autoscale, cost-cap reaction) | spec §G1 | KG-A/D/E/F1만 실행 가능. B/C 미구현 |
| **L1 ORFS docker 실 빌드** | — | 3개 fix 누적 push, 1+시간 빌드 미실행 (binary mv path 의심 동시) |
| **L1 LibreLane nix-build** | — | nix-build attribute 버그(Task #11)로 차단 |
| **L2 skill_library.query** | spec §3.2 | 미구현 (reversible-patch 저장소 자체가 없음) |
| **L2 typed-frontmatter memory write API** | spec §3.2 | recall만 있음. 운영 중 자동 write 경로 없음 |
| **L3 전체** | spec §G3 | License Gate(§13) 미진행으로 착수 보류 |
| **G4 reasoning trace 평가 (H3)** | spec §4.3 | trace 수집 schema(`trace.py`)만 있음, 외부 평가자(N≥5) 평가 인프라 없음 |
| **AWS Budgets alarm/log group** | ObservabilityStack | Budget만, alarm·dedicated log bucket은 Phase E 잔여 |

> publish/reframed/kill 분기 자체는 spec §5.3 canonical decision table이 단일 권위. 본 문서는 그 판단을 가능하게 하는 표면 상태만 보고한다.

---

## 5. 운영자 진입 경로 (cheat sheet)

새로 들어온 사람을 위한 최소 경로:

1. `make install` → `make test` (전체 통과 베이스라인 확인)
2. `make lint` (ruff 100자, py312 target)
3. `uv run semi-run --help` → CLI 표면 파악
4. `uv run graphify query "L1 process"` 또는 `make graph-serve` + MCP → spec/코드 cross-reference
5. AWS는 `semi-design-operator` SSO profile 필요 (`uv run semi-run auth login`)
6. CDK 변경: `cd cdk && npm test -- --runInBand`
7. 의문점은 `wiki/raw/sessions/` Q&A 또는 `graphify-out/GRAPH_REPORT.md`의 god node 우선

---

## 6. 다음 마일스톤 — 운영자 결정 영역

스냅샷이 말해주지 않는 한 가지: **2026-05-01 시점에서 다음 한 걸음으로 무엇을 잡아야 하는가.** 코드/spec만 봐서는 알 수 없는 운영 우선순위는 운영자(이 repo 주인)의 영역이다.

<!-- TODO(human): 아래 placeholder를 실제 우선순위 1-3개로 채워주세요. -->

> _placeholder — 다음 한 걸음과 그 이유를 한두 줄씩._
> 1. ...
> 2. ...
> 3. ...

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초판 작성 (as-built 스냅샷, L1 거의 완성 / L2 부분 / L3 미착수) |
