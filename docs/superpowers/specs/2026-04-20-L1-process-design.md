# L1 Process — Derived Spec

| | |
|---|---|
| 작성일 | 2026-04-20 |
| 작성자 | Jung Do Hyun (serithemage@gmail.com) |
| 상태 | Draft — Overview spec 승인됨, L1 구체화 단계 |
| Parent spec | `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` |
| Scope | L1 **Process** layer only. L2 Substrate · L3 Content는 별도 파생 spec |
| Authority 범위 | Overview spec의 §5.3 canonical decision table / §13 license gate / §7 program.md 규칙은 본 spec이 재정의하지 않는다. 참조만. |
| Reviews | Codex L1 1차 2026-04-20 (needs-major, 12건) → 12 fix. 2차 (needs-minor, REGRESSION 1 + new 5) → 6 fix. 3차 2026-04-20 (needs-minor, PARTIAL 2 + new 6) → (a) §4.1 `l1_lockfile_sha`/`full_lockfile_sha` 분리(L3 drift로부터 L1 cache key 보호), (b) §9 commit_shas를 L1 scope/L3-readiness scope 명시적 분리(null 허용), (c) §9.1 canonical-yaml hash 규칙 정의, (d) §10 KG-F를 F1(pre-RunTask rejection, paid job 0회) + F2(pytest mock) 분할, (e) §6.3 IAM `kms:Decrypt`를 explicit CMK ARN (StorageStack.bucketCmk + Secrets Manager CMK)로 scope, (f) §6.1 StorageStack에 `ObjectLockEnabled=true at creation` 명시, (g) §16.2 CDK 테스트에 Object Lock enabled 검증 추가, (h) `runner` extras에 `pydantic>=2,<3` 추가, (i) §7.2 `semi-run lockfile-verify` 출력 JSON 필드 완성 |
| K2 ζ 갱신 (2026-04-22) | LibreLane 2.4 → 3.0.2 (2026-04-02 tag, FOSSi Foundation) 전면 적용. Fargate ephemeral storage 10 GB 가정 → 200 GiB 정정. Step Functions는 Standard workflow 고정 (Express 5분 상한 초과 방지). Chipyard 1.13.0 (2024-09-30 이후 tag 없음) · Gemmini (2023-05 이후 tag 없음) SHA pin 재확인. 근거: `wiki/raw/papers/k2-zeta-l1-runtime.md` + `wiki/raw/imports_manifest.yaml` `axes.zeta.spec_contradictions_detected`. Dockerfile/CDK/plan 코드 레벨 반영은 별도 커밋(L1 구현 작업에 포함). |

---

## 1. 목적 (Why L1)

L1 Process는 **"L2·L3가 쓰는 재현 가능한 실험 실행 환경"**이다. 이 layer의 단독 가치는 다음 두 가지이며, 각각 §11 G1 exit criteria로 **scriptable assertion**되어야 한다(aspirational wording 금지):

- **재현성 보장**: `make lockfile-verify` + `scripts/kg/run-all.sh` 모두 exit 0인 상태. Efabless 셧다운·LibreLane rename·Gemmini `main` drift 같은 외부 변경으로부터 격리.
- **병렬 실험 substrate**: 1개 candidate = 1개 Fargate Spot task. SFN Map maxConcurrency=10. 상위 layer가 `L1.run(spec) → artifact`로만 사용.

L1 단독은 **overview §5.3 publish/kill 판정에 기여하지 않는다**. L2·L3가 동작하려면 L1이 먼저 green.

## 2. L1 범위

### 2.1 포함 (MVP)

| 구성요소 | 목적 |
|---|---|
| Docker images × 3 | orfs-runner / librelane-runner / metric-collector |
| CDK TypeScript stacks × 6 | Network / Storage / Container / Compute / Workflow / Observability |
| Python orchestrator CLI (`semi-run`) | 로컬에서 AWS SFN 호출, artifact 수집, DDB 조회 |
| Pydantic schemas (tagged unions) | `Spec` / `RunArtifact` / `FlowParameters` / `ResourceOverrides` / `ExperimentalParameters` |
| Makefile (`make run`) | 1-job end-to-end 실행 |
| `lockfile.yaml` | SHA + container digest + source tarball mirror (overview §6.2 필드명 정합) |
| Kill-gate verification scripts | KG-A~KG-E **deterministic** 검증 (overview §8 완화) |
| CDK test suite | snapshot + cdk-nag (§16) |

### 2.2 제외

- L2: memory system, skill library, QMD, `L2.lint` 확장, findings/failures 자동 생성
- L3: RTL 생성 에이전트, Open-Ideation Planner, MLPerf Tiny harness, **functional simulation**
- 실물 테이프아웃 (Iter 3+)
- LLM 호출 자동화 (L1은 infra. spec.yaml은 외부 주입)
- `wiki-lint` 확장 (Phase 1a engine 그대로)
- **Chipyard + Gemmini 전체 빌드** (G1 gcd에 불필요 — Codex #4 반영. L3 readiness에서 KG로 이관)

## 3. Architecture (L1 내부 구조)

```
Local (developer machine)
 └─ semi-run CLI (uv + boto3) ──┐
                                │ (1) spec.yaml → S3 (staging/)
                                │ (2) SFN StartExecution
                                ▼
AWS (CDK TypeScript provisioned)
 ┌───────────────────────────────────────────────────────────┐
 │ WorkflowStack                                             │
 │   Step Functions Standard Workflow                        │
 │   ValidateSpec Lambda (G1-scope rejection)                │
 │   Map state (maxConcurrency=10)                           │
 │     per-candidate sub-workflow:                           │
 │     ┌─ rtl-build (Fargate Spot)  ← semi/orfs-runner       │
 │     ├─ synth     (Fargate Spot)  ← semi/orfs-runner       │
 │     ├─ pnr       (Fargate Spot)  ← orfs OR librelane      │
 │     ├─ sim       Pass placeholder (L3에서 활성화)         │
 │     ├─ signoff   (Fargate Spot)  ← semi/orfs-runner       │
 │     └─ metrics   (Fargate Spot)  ← semi/metric-collector  │
 │     └─ finalize  (Lambda, per-object atomic)              │
 │         1. ValidateManifest (all stage outputs present)   │
 │         2. CopyObject staging/→final/ **with retention    │
 │            header** (GOVERNANCE mode, retain-until=90d)   │
 │         3. PutObject sidecars (metrics/provenance/cost)   │
 │            **with same retention header**                 │
 │         4. PutObject _SUCCESS last **with retention hdr** │
 │         5. DDB Candidates update (ddb_write_count 포함)   │
 └───────────────────────────────────────────────────────────┘
 S3 artifact lake  |  DynamoDB (4 tables)  |  ECR (3 repos)
```

**G1 correctness boundary (Codex #11 반영)**: `sim` stage가 Pass placeholder이므로 **G1 sign-off clean artifact는 functional correctness evidence가 아니다**. 이후 어떤 downstream claim(H1b "non-knob structural patch" 포함)도 "gcd가 G1에서 sign-off clean이므로 설계가 올바르다"라 주장할 수 없다. Functional correctness는 L3 simulate 활성화 이후에만 가능.

## 4. Interface Specification

### 4.1 `L1.run(spec_uri)` contract (overview §3.2 구현)

**Input** — S3 URI to `spec.yaml` (Pydantic `Spec` serialized). `parameters`는 **tagged union**으로 제한되어 L2/L3 breaking change를 막는다 (Codex #1):

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from datetime import datetime

# 모든 모델에 Extra.forbid 강제 (Codex 2차 consistency 지적)
class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

class FlowParameters(_StrictBase):
    """Tool-flow knobs — bounded namespace. 부록 C exclusion list 전용."""
    core_utilization: float | None = None          # ORFS CORE_UTILIZATION
    place_density: float | None = None
    clock_period_ps: int | None = None
    global_routing_iterations: int | None = None
    timing_driven: bool | None = None
    synth_flatten: bool | None = None
    # additional knobs added via minor version bump (schema version +0.1)

class ResourceOverrides(_StrictBase):
    """Fargate TaskDef override"""
    cpu_units: int | None = None                    # 4096 default
    memory_mb: int | None = None                    # 16384 default
    ephemeral_storage_gb: int | None = None         # 21 default (Codex #8)

class ExperimentalParameters(_StrictBase):
    """L3-only: reviewer-audited ad-hoc patches. L1은 pass-through + metadata 로깅만."""
    patch_uri: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

class Spec(_StrictBase):
    version: int = 1                                # breaking → major bump
    run_id: str                                     # ULID, client 생성
    design: Literal["gcd", "ibex", "aes"]           # schema-level; ValidateSpec Lambda가 G1에선 gcd만 허용
    stack: Literal["orfs", "librelane"]
    flow_parameters: FlowParameters
    resource_overrides: ResourceOverrides = Field(default_factory=ResourceOverrides)
    experimental: ExperimentalParameters = Field(default_factory=ExperimentalParameters)
    compute_budget_usd: float                       # 상한 $
    planned_cost_per_stage_usd: dict[
        Literal["rtl-build","synth","pnr","signoff","metrics"], float
    ] = Field(default_factory=dict)
    seed: int
    l1_lockfile_sha: str                            # canonical hash over --scope l1 projection (L1 cache key, L3 drift와 무관)
    full_lockfile_sha: str | None = None            # optional, --scope full 포함 시 기록 (L3 readiness run에만 사용)
```

**"experimental namespace 외 arbitrary key 금지"** — `_StrictBase.model_config = ConfigDict(extra="forbid")`가 상속을 통해 모든 sub-model에 적용. 새 정식 knob은 `FlowParameters`에 field 추가 + minor version bump로만. `ExperimentalParameters.metadata: dict[str, str]`은 의도적 이탈구로 **문자열 key/value만 허용** — nested object는 불가.

**Output** — S3 URI to artifact bundle `s3://{bucket}/runs/{run_id}/final/`:

```
runs/{run_id}/
├── staging/                   # 중간 산출물 (finalize 이전)
│   └── (stage outputs)
└── final/                     # finalize 이후, Object Lock governance
    ├── spec.yaml              # 입력 복사본 (immutable)
    ├── _SUCCESS               # 최종 marker
    ├── rtl/*.v
    ├── synth/{*.v,*.rpt}
    ├── pnr/{*.def,*.rpt}
    ├── signoff/{sta.rpt, drc.rpt, lvs.rpt}
    ├── metrics.json           # RunArtifact schema
    ├── provenance.yaml        # license + SHA + agent/operator ID (overview §13)
    ├── cost_actuals.json      # stage별 실비용 (Codex #10)
    └── logs/                  # stage별 stdout/stderr
```

`cost_actuals.json`은 `RunArtifact.cost_breakdown`(list[StageTiming]) serialization이며, 동일한 필드 의미를 갖는다 (Codex 2차 consistency).

```python
class StageTiming(_StrictBase):
    stage: Literal["rtl-build","synth","pnr","signoff","metrics"]
    started_at: datetime
    ended_at: datetime
    exit_code: int
    cost_usd: float
    fargate_vcpu: int
    fargate_memory_mb: int

class RunArtifact(_StrictBase):
    run_id: str
    spec_uri: str
    status: Literal[
        "clean", "drc_fail", "lvs_fail", "sta_fail",
        "tool_crash", "spot_reclaimed_max", "rejected_not_in_g1",
        "budget_exceeded", "in_progress",
    ]
    metrics: "Metrics | None"                       # None if status != clean
    metrics_uri: str
    reports: list[str]
    provenance_uri: str
    l1_lockfile_sha: str                             # 대응 Spec.l1_lockfile_sha
    full_lockfile_sha: str | None = None
    cost_usd: float                                  # total
    cost_breakdown: list[StageTiming]
    ddb_write_count: int                             # app-level counter (Codex #7)
    started_at: datetime
    ended_at: datetime | None

class Metrics(_StrictBase):
    area_um2: float
    power_mw: float | None
    max_freq_mhz: float | None
    wns_ns: float | None
    tns_ns: float | None
    drc_violations: int
    runtime_s: float
    # functional fields 없음 — G1에서 simulation 부재 (Codex #11)
```

### 4.2 Error taxonomy

| Error | 발생 stage | 처리 | 결과 status |
|---|---|---|---|
| `SpotReclaimed` | any Fargate | Retry MaxAttempts=2, BackoffRate=2 (KG-D) | 초과 시 `spot_reclaimed_max` |
| `OOM` | rtl-build/pnr | Retry 1회 with 2× CPU/memory | 실패 시 `tool_crash` |
| `TimingFail` | signoff | Catch → record → end | `sta_fail` |
| `DRCFail` | signoff | Catch → record → end | `drc_fail` |
| `LVSFail` | signoff | Catch → record → end | `lvs_fail` |
| `ToolCrash` | any | Catch → record → DLQ | `tool_crash` |
| `RejectedNotInG1Scope` | ValidateSpec | 즉시 reject, SFN 종료 | `rejected_not_in_g1` |
| `BudgetExceeded` | pre-stage check (`semi-run cost` + §10.6 guard) | `Spec.compute_budget_usd`와 누적 `cost_breakdown` 합 비교, 초과 시 SFN AbortExecution | `budget_exceeded` |
| `Unknown` | any | SQS DLQ + SNS alarm | `tool_crash` |

### 4.3 Immutability via per-object finalization (Codex 2차 REGRESSION #9 재반영)

Object Lock은 **각 final object의 `PutObject`/`CopyObject` 시점에 retention과 함께** 걸린다. `_SUCCESS`를 마지막에 쓰고 이후 Object Lock을 별도 단계로 적용하면, 두 단계 사이 failure 시 **mutable "성공" artifact**가 남는 regression이 발생한다. 그래서 다음과 같이 per-object 패턴을 사용:

1. **stage outputs → `runs/{run_id}/staging/{stage}/`** (mutable prefix, versioning on). staging은 lock 없음.
2. **ValidateManifest Lambda**가 모든 required stage 산출물(`signoff/*.rpt`, 각 stage 출력) 존재 확인.
3. **Copy to final with retention**: 각 승인된 object를 `runs/{run_id}/final/` prefix로 S3 CopyObject. 이 때 **모든 put/copy 호출에 `x-amz-object-lock-retain-until-date` + `x-amz-object-lock-mode=GOVERNANCE`** 헤더 포함 (단일 호출 내 atomic). 실패 시 부분 copy된 object도 이미 lock 상태 — mutable 잔재 불가.
4. **Write sidecars with retention**: `metrics.json`, `provenance.yaml`, `cost_actuals.json` → final/. 각 put은 위 retention 헤더 포함. `cost_actuals.json`은 `RunArtifact.cost_breakdown` list의 serialization.
5. **Write `_SUCCESS` with retention (last)**: `_SUCCESS` put 자체도 동일 retention 헤더 포함. `_SUCCESS` 존재 = 모든 이전 object가 이미 locked라는 invariant가 성립.
6. **실패 시 staging 보존, final/은 부분 생성 가능**. `_SUCCESS`가 없으면 Reader는 해당 run을 미완료로 간주(R1 idempotency). 부분 locked final/은 mutable 문제 없음 — 다음 run은 별도 `run_id`로 생성되므로 conflict 없음.

이 sequence는 `finalize` Lambda에서 수행. "post-hoc batch object-lock"은 금지.

## 5. Docker Images (ECR)

모두 `latest` 태그 금지, SHA256 digest로만 참조. `lockfile.yaml.container_digests`에 기록.

| Repo | Base | 설치 | 예상 크기 | 주 용도 |
|---|---|---|---|---|
| `semi/orfs-runner` | `debian:12-slim` | ORFS (SHA pinned) + OpenROAD + Yosys 0.55 + open_pdks sky130A | ~2.5GB | `rtl-build`, `synth`, `pnr(orfs)`, `signoff` |
| `semi/librelane-runner` | LibreLane 3.0.2 공식 Nix | LibreLane 3.0.2 SHA-pinned + sky130A | ~4GB | `pnr(librelane)` |
| `semi/metric-collector` | `python:3.12-slim` | `semi_design_runner.metrics` 모듈 (동일 Python 코드, 컨테이너는 wheel 설치) | ~150MB | `metrics` stage |

**Codex #8 반영 — Verilator 제외**: G1 scope가 functional simulation을 포함하지 않으므로 `orfs-runner`에서 Verilator 제거. L3 활성화 시 `semi/sim-runner` 신설.

**Codex #8 반영 — Double-maintenance 방지**: `metric-collector` 이미지는 `semi_design_runner.metrics` Python 모듈을 wheel로 설치. 즉 파서 구현은 **패키지 한 곳에만 존재**하며 컨테이너 ENTRYPOINT가 wheel 모듈을 호출.

**Entry contract**: 환경변수 `RUN_ID`, `STAGE`, `INPUT_S3_URI`, `OUTPUT_S3_URI`, `SIMULATE_SPOT_RECLAIM` (test only, §10 KG-D).

## 6. CDK Stacks (TypeScript)

`cdk/` 디렉토리 신설. Node 20+ / TypeScript / `aws-cdk-lib@^2`. 환경 분리 `--context env=dev|prod`. 전 stack에 `cdk-nag` (§16).

### 6.1 Stack 구성

| Stack | 생성물 | 의존 |
|---|---|---|
| `NetworkStack` | VPC + private subnets × 2 AZ. **VPC endpoints (Codex #8 + 2차 new #2)**: `com.amazonaws.{region}.s3` (Gateway, free), `ecr.api`, `ecr.dkr`, `logs`, `secretsmanager`, `ssm`, `sts`, `monitoring`, **`kms`** (§6.3 KMS decrypt 경로 필요). NAT gateway **없음** | — |
| `StorageStack` | S3 bucket `semi-design-{account}-{region}` (**versioning on + `ObjectLockEnabled=true` at creation**[S3 요구사항 — 사후 설정 불가, Codex 3차 new #6], Object Lock governance, lifecycle 90d → Glacier IR) + DynamoDB × 4 + KMS CMK (`bucketCmk`) | — |
| `ContainerStack` | ECR × 3 repos (scan on push, immutable tags, image tag mutability `IMMUTABLE`). 큰 이미지 pull 최적화는 **pull-through cache** 옵션(§14) | — |
| `ComputeStack` | ECS cluster (no EC2) + Fargate TaskDef × 3 (4vCPU/16GB base, **ephemeral storage 21GB** explicit, override via SFN input) | Network + Container |
| `WorkflowStack` | SFN Standard Workflow + Map state + Lambda × 3 (`ValidateSpec`, `InitGeneration`, `Finalize`) + EventBridge rules | Compute + Storage |
| `ObservabilityStack` | CloudWatch dashboards (Spot reclaim rate, SFN failure rate, cost, **per-candidate `ddb_write_count`**) + alarms ($50 / $100 budget, Spot fail > 30%, cost/candidate > $5) | Storage |

> **Naming convention** (2026-05-25 amendment): 위 6 stack은 `bin/semi-design.ts` 인스턴스화 시 `semi-design-${env}-` prefix가 자동 적용됨 (예: `semi-design-dev-NetworkStack`). 본 prefix는 deployment account 내 sibling 프로젝트와의 CloudFormation 이름 충돌을 차단한다 (예: Roboco 779411790546은 `serverless-openclaw` 프로젝트가 bare `StorageStack` / `NetworkStack`을 이미 점유). 본 amendment는 *naming convention 추가*이지 spec §5.4 정량 임계값 / §6.1 stack 구성 / §6.2 schema 재정의 0건 (Learnings #1 invariant 정합).

### 6.2 DynamoDB 스키마 (Codex #7 반영)

| Table | PK | SK | Key attributes |
|---|---|---|---|
| `Runs` | `run_id` | — | `spec_uri`, `status`, `total_cost_usd`, `lockfile_sha`, `started_at`, `ended_at` |
| `Generations` | `run_id` | `gen#{N}` | `population_uri`, `cost_usd` (L2/L3 write-through; L1은 `N=0`만) |
| `Candidates` | `run_id` | `gen#{N}#cand#{K}` | `params`, `stage_status`, `metrics_uri`, `sfn_execution_arn`, `ddb_write_count: int` (app-counter), `cost_breakdown: list` |
| `Events` | `run_id` | `ts#{iso}` | `kind`, `payload`, TTL 90d |

**App-level counter (Codex #7)**: 모든 DDB write wrapper(`aws/ddb.py::put_with_count`)가 `Candidates.ddb_write_count`를 increment. KG-E 스크립트가 run 종료 후 이 값을 읽어 <50 확인. CloudWatch에 의존하지 않음.

### 6.3 IAM

- **Fargate task role**: `s3:Get/PutObject runs/*`, `dynamodb:PutItem/UpdateItem Candidates/Events`, `secretsmanager:GetSecretValue /semi-design/*` (KG-C2 전용 task role만), **`kms:Decrypt` scoped to explicit CMK ARNs** (`StorageStack.bucketCmk` + Secrets Manager 기본 KMS key), `logs:CreateLogStream/PutLogEvents`. Bare `kms:Decrypt *` 금지 (Codex 3차 new #5).
- **Lambda role (Finalize)**: `s3:Copy/PutObject/PutObjectRetention`, `dynamodb:UpdateItem Candidates/Runs`.
- **SFN role**: `ecs:RunTask`, `lambda:Invoke`, `dynamodb:PutItem Events`.
- **Operator role (`semi-design-operator`)**: IAM Identity Center (SSO) 권장, session 8h. `AssumeRole` from local CLI.

## 7. Python Orchestrator CLI (`semi-run`)

### 7.1 패키지 레이아웃

기존 `src/semi_design_wiki/`와 별도. Single source for metric parser (Codex #8):

```
src/semi_design_runner/
├── __init__.py
├── cli.py                 # click entry point (semi-run)
├── schemas.py             # Pydantic (Spec, RunArtifact, Metrics, StageTiming, FlowParameters, ResourceOverrides, ExperimentalParameters)
├── aws/
│   ├── __init__.py
│   ├── clients.py         # boto3 session/client factory with profile/SSO
│   ├── s3.py
│   ├── ddb.py             # put_with_count wrapper
│   └── sfn.py
├── trace.py               # JSONL trace (~/.cache/semi-run/traces/{run_id}.jsonl)
├── lockfile.py
├── metrics.py             # .rpt/.def parser — source of truth
└── cost.py                # CloudWatch-based cost attribution + budget guard
```

`pyproject.toml` 엔트리: `semi-run = "semi_design_runner.cli:main"`. `[project.optional-dependencies]` 에 `runner = ["boto3", "click", "ulid-py", "pydantic>=2,<3"]` (§4.1이 `ConfigDict` Pydantic v2 syntax 사용. Phase 1a 기존 deps와 v2 정합성을 plan 작성 시 확인).

### 7.2 CLI commands

| Command | 기능 |
|---|---|
| `semi-run init --spec spec.yaml` | Pydantic validate + S3 put + DDB Runs 생성. `run_id` 반환 |
| `semi-run submit --run-id <id>` | SFN StartExecution |
| `semi-run status --run-id <id> [--wait]` | DDB + SFN DescribeExecution 결합 |
| `semi-run artifacts --run-id <id> --dest <dir>` | S3 `final/` 다운로드 |
| `semi-run lockfile-verify [--scope l1|full]` | lockfile.yaml SHA와 실제 upstream commit 대조 → JSON `{verified, mismatched, deferred_l3, scope, l1_lockfile_sha}` (Codex 3차 internal consistency) |
| `semi-run cost --run-id <id>` | CloudWatch 기반 실비용 + planned 대비 diff |
| `semi-run auth login` | IAM Identity Center SSO helper (aws sso login wrapper) |

### 7.3 JSONL infra trace

모든 boto3 호출과 SFN state transition을 `~/.cache/semi-run/traces/{run_id}.jsonl`에 append. L3 reasoning-trace와 분리된 **infrastructure trace** (debug용).

## 8. Makefile

기존 `make install / test / lint / fmt / clean` 유지. 신설:

```makefile
DESIGN ?= gcd
STACK  ?= orfs
SEED   ?= 42

run: lockfile-verify
	uv run semi-run init --spec specs/$(DESIGN)-$(STACK).yaml --seed $(SEED)
	uv run semi-run submit --run-id $$(cat .last-run-id)
	uv run semi-run status --run-id $$(cat .last-run-id) --wait

lockfile-verify:
	uv run semi-run lockfile-verify

kg-all:
	bash scripts/kg/run-all.sh

.PHONY: run lockfile-verify kg-all
```

`specs/gcd-orfs.yaml`, `specs/gcd-librelane.yaml`이 MVP 샘플. `specs/ibex-*.yaml`, `specs/aes-*.yaml`은 **schema 예시로만** 존재하며 ValidateSpec이 G1 단계에선 reject.

## 9. `lockfile.yaml` 구조 (overview §6.2 정합 — Codex #3)

리포 루트. 변경은 별도 PR + CI 재검증. **필드명은 overview와 정확히 일치**:

```yaml
version: 1
updated_at: 2026-04-20
updated_by: serithemage
commit_shas:                                # overview 필드명 그대로 (was: upstream_shas)
  # --- L1 scope (G1 필수) ---
  openroad:       "<SHA to be filled at G1 implementation>"
  librelane:      "<SHA>"
  yosys:          "<SHA>"
  open_pdks:      "<SHA>"
  # --- L3-readiness scope (G1에선 null 허용) ---
  verilator:      null                      # L3에서 사용
  cocotb:         null                      # L3에서 사용
  chipyard:       null                      # L3에서 사용
  gemmini:        null                      # L3에서 사용
  mlcommons_tiny: null                      # L3에서 사용
container_digests:
  orfs-runner:        "sha256:<digest>"
  librelane-runner:   "sha256:<digest>"
  metric-collector:   "sha256:<digest>"
source_tarball_mirrors:                     # overview 필드명 그대로 (was: source_mirrors)
  openroad: "s3://semi-design-{account}-{region}/mirrors/openroad/{sha}.tar.gz"
  librelane: "s3://.../mirrors/librelane/{sha}.tar.gz"
  # ... 모든 commit_shas 항목에 1:1 대응 mirror
pdk_digests:
  sky130A: "sha256:<digest>"
stale_source_policy:
  grace_period_hours: 24
  action_on_failure: ci_red
ci_verification:
  last_green_commit: "<git SHA>"
  last_green_at: 2026-04-20T00:00:00Z
```

**SHA 값은 G1 구현 단계에서 실측 채움**. spec 단계는 스키마 확정만.

### 9.1 Lockfile scope 분리 + hash 안정성 (Codex 2차 new #3 + 3차 개선)

`commit_shas`는 L1과 L3-readiness SHA가 한 파일에 섞여 있다. G1에서 `make lockfile-verify`가 L3-only SHA까지 강제 검증하면 **G1 단계에서 항상 fail**한다. 또한 L3 SHA가 나중에 채워질 때 전체 파일 hash가 변해 L1 cached runs가 무효화되는 drift 문제가 있다. 따라서 **scope flag + 별도 hash** 도입:

**Scope 분리** (Codex 3차 new #2 반영):
- **L1 scope**: `openroad`, `librelane`, `yosys`, `open_pdks` + all `container_digests` + `pdk_digests`. 이것만 G1에서 green 필수.
- **L3-readiness scope**: `verilator`, `cocotb`, `chipyard`, `gemmini`, `mlcommons_tiny`. G1에선 `null` 허용, L3 파생 spec 착수 시점에만 채움.

**CLI 동작**:
- `semi-run lockfile-verify --scope l1` (default): L1 scope만 verify. 출력 JSON:
  ```json
  {
    "verified": true,
    "mismatched": [],
    "deferred_l3": ["chipyard", "gemmini", "mlcommons_tiny", "verilator", "cocotb"],
    "scope": "l1",
    "l1_lockfile_sha": "sha256:<hash>"
  }
  ```
- `semi-run lockfile-verify --scope full`: L1 + L3-readiness 모두. 실패 시 `deferred_l3` 없이 `mismatched`로 보고.
- §11 **G1 exit criterion 6**은 `--scope l1`만 녹색이면 pass (`deferred_l3`는 영향 없음).

**Hash 분리 (Codex 3차 new #1 반영)**:
- `l1_lockfile_sha = sha256(canonical_yaml(l1-scope projection))`. L3 SHA가 `null`이든 채워지든 동일 값. L1 cached runs의 cache key로 안전.
- `full_lockfile_sha = sha256(canonical_yaml(전체 lockfile))`. L3 readiness run에서만 사용. L3 SHA drift 시 변경됨 (의도적).
- Canonical YAML = key 알파벳 정렬 + L3-readiness 항목 중 `null`은 제외. 이 규칙으로 L3 항목이 `null`→ SHA 채워질 때에도 `l1_lockfile_sha`는 불변.

## 10. Kill-Gate Verification (Codex #4, #5, #6 대응)

모든 스크립트는 `scripts/kg/` 디렉토리. 각각 **deterministic**하며 JSON 결과(`passed: bool`, `measurements: {}`) 출력.

### KG-A — LibreLane 3.0.2 on Fargate Spot
- Script: `scripts/kg/kg-a-librelane-fargate.sh`
- 측정: gcd flow 완주 시간, image pull time, peak ephemeral storage 사용량
- **성공 기준**: timeout 30분 내 `_SUCCESS` + ephemeral storage peak < 21 GB (Fargate 한도 200 GiB 여유, K2 ζ 검증값) + image pull < 10분
- 실패 시 fallback: pure ORFS stack (OpenROAD + Yosys 직접)으로 다운그레이드, `stack=librelane` 옵션 제외. 이 fallback 경로도 스크립트가 자동 검증.

### KG-B — Chipyard prebuilt cache integrity (L3-readiness only, G1 exit 필수 아님)
- Script: `scripts/kg/kg-b-chipyard-cache.sh`
- **Chipyard 전체 빌드는 G1 범위 밖** (Codex #4 반영). 대신 L3에서 쓸 S3 prebuilt cache의 **메타데이터 무결성**만 검증.
- 측정: S3 object layout (`s3://.../chipyard-prebuilt/{sha}/chipyard.tar.gz`) + SHA256 + producer command 기록 (`producer.yaml` with cdk version, build host, command) + invalidation rule (`chipyard` commit_sha 변경 시 재생성)
- **성공 기준**: `s3://.../chipyard-prebuilt/{lockfile.commit_shas.chipyard}/` 에 `chipyard.tar.gz` + `producer.yaml` + `sha256` 파일 존재, SHA 일치
- **KG-B 통과는 G1 exit의 prerequisite이 아님** — L3 readiness gate로 표기(§11).

### KG-C — SDK budget & quota (two-stage, Codex #5 + 2차 new #4)
- Script A: `scripts/kg/kg-c1-token-budget.sh` — **deterministic** local token count (anthropic-tokens, tiktoken). 실 호출 0. 성공: predicted tokens < monthly budget × safety factor.
- Script B: `scripts/kg/kg-c2-live-smoke.sh` — **optional** live quota smoke. 1회 실제 호출 (최소 prompt), rate limit header 관찰. 성공: 429 없음 + remaining quota > threshold. **CI에서 weekly만** 실행.
- **실행 경로 (Codex 2차 new #4 반영)**: KG-C2는 §13 원칙(로컬 CLI는 secrets 접근 불가)과 충돌하지 않도록 **Fargate Spot task로 실행**. CDK에 별도 TaskDef `kg-c2-smoke` + 전용 task role에 `secretsmanager:GetSecretValue` grant. GitHub Actions CI는 `aws ecs run-task`로 이 task를 trigger만 하고 secrets 자체에 닿지 않는다. 로그는 CloudWatch redaction filter로 key 마스킹.
- **Secrets**: Claude/Codex API key는 AWS Secrets Manager `/semi-design/{provider}-api-key`. grant 대상은 KG-C2 TaskDef task role 한 곳만.
- **성공 기준**: KG-C1 pass는 G1 필수. KG-C2는 옵션 (실패 시 경고만, G1 exit 차단 아님).

### KG-D — Spot reclaim deterministic test (Codex #6)
- Script: `scripts/kg/kg-d-spot-reclaim.sh`
- **메커니즘**: 테스트 컨테이너가 `SIMULATE_SPOT_RECLAIM=1` 환경변수를 받으면 sleep N초 후 SIGTERM(exit 143) 반환. SFN retry 정책이 이를 `SpotReclaimed` 오류와 동일 패턴으로 처리.
- 측정: 10개 test job(각각 simulated reclaim 1회 주입) 중 완주율. 실제 Spot interruption 관측은 별도 **production smoke** (KG-D-prod, 옵션).
- **성공 기준**: 완주율 ≥ 80% (10개 중 8개 이상).

### KG-E — DDB write amplification via app-counter (Codex #7)
- Script: `scripts/kg/kg-e-ddb-write-amp.sh`
- **측정**: CloudWatch 대신 **app-level counter** (`Candidates.ddb_write_count`). Script가 run 종료 후 DDB 조회.
- **성공 기준**: candidate 1개당 `ddb_write_count < 50`. MVP 실측 예상 = stage당 1 event + finalize 시 Candidates put + Runs update ≈ 8.

### KG-F — Budget guard assertion (Codex 2차 #10 + 3차 new #3 반영: paid-run 없이 verify)
**원칙**: 실제 Fargate RunTask를 호출해 abort를 증명하는 circular test는 금지(비용 소비). 대신 두 층을 분리해서 검증:

- Part F1 — **Pre-RunTask rejection** (no paid job):
  - `semi-run init`/ValidateSpec Lambda가 `sum(Spec.planned_cost_per_stage_usd.values())` > `Spec.compute_budget_usd` 또는 월 누적 > `scripts/kg/budget-limits.yaml` 한도이면 **RunTask 호출 전에** `RejectedByBudgetGuard` 반환.
  - Test: `kg-f1-prebudget.sh`가 `compute_budget_usd=0.01`, `planned_cost_per_stage_usd.total=5.0` spec을 제출 → `semi-run init`이 exit code 비영·JSON `{ rejected: true, reason: "planned_cost_exceeds_budget" }` 반환. **ECS/SFN 호출 0회**.
- Part F2 — **Post-stage accumulator unit test** (mocked):
  - Lambda `Finalize` or stage-completion handler 내부 로직(`accumulated_cost_breakdown_sum > compute_budget_usd`)을 pytest로 단위 테스트. boto3 호출은 mock. 실 Fargate 비용 0.
  - Test: `uv run pytest tests/test_budget_guard.py -v`에서 abort 조건·status 전이 검증.

- **성공 기준**: F1 스크립트 `{ passed: true }` + F2 pytest `{ passed: true }`. 합쳐서 KG-F pass.

### KG 일괄 실행
- `scripts/kg/run-all.sh`: KG-A, KG-C1, KG-D, KG-E, KG-F **필수**. KG-B는 L3 readiness 단계로 분리. KG-C2는 옵션.
- 각 script JSON 결과를 `artifacts/kg-reports/{date}/`에 보관.

## 11. G1 Exit Criteria (scriptable assertions — Codex aspirational wording 지적)

아래 전부 만족 시 G1 통과 → L2/L3 파생 spec 착수 허가. 각 항목은 **단일 명령어로 exit code 0 + JSON pass** 형태:

| # | Assertion | Command | Pass JSON |
|---|---|---|---|
| 1 | gcd ORFS 완주 | `make run DESIGN=gcd STACK=orfs` | `{status: clean, metrics: {...}}` in DDB |
| 2 | gcd LibreLane 완주 | `make run DESIGN=gcd STACK=librelane` | 동일 |
| 3 | Artifact bundle + marker | `aws s3 ls s3://.../runs/{id}/final/_SUCCESS` | exit 0 |
| 4 | Metrics schema valid | `uv run semi-run artifacts --run-id ... && python -m semi_design_runner.schemas validate artifacts/metrics.json` | `{valid: true}` |
| 5 | `semi-run status` 정상 | `uv run semi-run status --run-id ...` | exit 0, status=clean |
| 6 | Lockfile L1 scope verify | `make lockfile-verify` (= `semi-run lockfile-verify --scope l1`) | `{verified: true, mismatched: [], deferred_l3: ["chipyard","gemmini","mlcommons_tiny","verilator","cocotb"], scope: "l1", l1_lockfile_sha: "sha256:..."}` |
| 7 | KG-A·C1·D·E·F pass | `make kg-all` | 각 script `{passed: true}` |
| 8 | Test coverage ≥85% | `uv run pytest --cov=src/semi_design_runner --cov-fail-under=85` | exit 0 |
| 9 | Clean VM reproducibility | GitHub Actions CI (ephemeral) `make install && make test && make run DESIGN=gcd STACK=orfs` | 모든 job green |

**KG-B (Chipyard prebuilt cache)는 G1 exit 필수 아님** — L3 readiness gate로 분리 (Codex #4).

## 12. 비목표 (Non-goals)

- L2 memory system / skill library / QMD
- L3 RTL agent / Open-Ideation planner / functional simulation
- **ibex·aes 실행** — Spec.design Literal에 포함되지만 **ValidateSpec Lambda가 G1에서 reject** (Codex #2). G1 exit 이후 rejection 제거.
- Chipyard/Gemmini 전체 빌드 (G1은 cache 무결성만)
- Reasoning trace logging (L3 novelty artifact)
- Dashboard UI (issues/004 따라 L1/L3 결정 후)

**ValidateSpec rejection 구현 요구 (Codex #2)**:
```python
def validate(spec: Spec) -> None:
    if spec.design != "gcd":
        raise RejectedNotInG1Scope(
            f"design={spec.design} is not in G1 scope; allowed: [gcd]"
        )
```
Pytest로 rejection path 테스트 필수 (§16 CDK tests 별도).

## 13. 외부 의존성 · 선행 조건 (secrets 포함 — Codex #5, #12)

- **AWS 계정**: `semi-design-operator` 역할 + IAM Identity Center SSO. Session 8h.
- **AWS Secrets Manager** (Codex #5): `/semi-design/claude-api-key`, `/semi-design/codex-api-key`. IAM으로 Fargate task role에만 read grant. 로컬 CLI는 **접근 불가** (원칙: secret은 AWS 내부에서만).
- **Node.js 20+** (CDK), **Python 3.12 + uv**, **Docker Desktop**.
- **Fargate Spot vCPU quota**: dev 계정은 32 vCPU, prod는 사전 증설 요청 (§14).
- **ECR pull-through cache** (옵션): 4GB librelane-runner repeat pull 최적화용. `lockfile.yaml`이 digest로 pin하므로 캐시 hit ratio 높음.

## 14. 리스크 · 대응 (Codex #12 반영 보강)

| 리스크 | 대응 |
|---|---|
| LibreLane 3.0.2 Nix가 Fargate 미지원 | KG-A 조기 감지. 실패 시 pure ORFS stack으로 다운그레이드, `stack=librelane` exclusion |
| **Fargate Spot vCPU account quota 부족** | CDK deploy 전 `scripts/preflight-quota.sh`로 확인. dev=32, prod=사전 증설 |
| Spot 회수율 리전 차이 | KG-D를 us-east-1, us-west-2에서 실행. 회수율 높은 리전 제외 |
| DDB 비용 | Events TTL 90d 엄격. Candidates GSI 재검토. KG-E로 write amp 모니터링 |
| **CDK context drift (dev/prod)** | `cdk.context.json`을 git에 commit. PR마다 `cdk synth` diff 필수 |
| **ECR pull rate limit** | Pull-through cache 옵션 + lockfile digest pin으로 re-pull 최소화 |
| **KMS policy 오류** | CMK의 key policy에 Fargate task role `kms:Decrypt` 명시. CDK에 `cdk-nag`로 검증 |
| **ORFS upstream breaking change mid-Iter** | `lockfile.yaml` commit_sha 고정. Iter 내 upstream 변경 무시. CI가 stale source 자동 alert |
| Gemmini `main` drift | `commit_shas.gemmini`로 고정 |
| LLM 비용 폭주 | KG-C1 token budget check + Budget 알람 $50/$100 |
| L2 substrate 구현 난도 | 본 L1 spec의 범위 밖 (제외) |
| Efabless 대체 경로 불확실 | Iter 1은 sign-off 시뮬레이션까지만. 실물 Iter 3+ |
| **Rollback: CDK mid-stack 실패** | Stack별 `--require-approval broadening` + CDK Changeset preview. 실패 시 `cdk destroy` 단일 stack 단위 |
| **CLI auth 복잡도** | `semi-run auth login` wrapper 제공, 내부는 `aws sso login`. Session token 만료 8h, 자동 재발급 X (명시적 logout) |
| **Log 보관 정책 누락** | CloudWatch Logs retention 30d 기본, `artifacts/kg-reports/`는 S3 90d |
| **Secrets 로그 유출** | 모든 Fargate log에 대해 CloudWatch Logs subscription filter로 API key 패턴 차단 (`redaction` pattern) |

## 15. 향후 확장 훅 (L2/L3 연결 지점)

- `Spec.experimental.patch_uri`는 L3 Open-Ideation의 non-knob structural patch 전달 경로
- `RunArtifact.reports` URI는 L2.lint의 input
- SFN `simulate` Pass state는 L3가 활성화 (이때 `semi/sim-runner` 이미지 신설, Verilator 포함)
- `provenance.yaml`은 overview §13 License Gate 실행 포인트

## 16. CDK Test Strategy (Codex #12 신설)

`cdk/test/` 디렉토리. CDK deploy 전 모든 PR에 필수:

### 16.1 Snapshot tests (`aws-cdk-lib/assertions`)
- 각 stack마다 `Template.fromStack(stack).toJSON()` 스냅샷
- PR에서 diff 변화 있으면 reviewer 승인 필요

### 16.2 Unit assertions
- `template.hasResource('AWS::S3::Bucket', { Properties: { ... } })` 형식
- 필수 설정 검증: versioning on, **`ObjectLockEnabled: true` at creation** (Codex 3차 new #6), `ObjectLockConfiguration.DefaultRetention.Mode = GOVERNANCE`, KMS encryption, VPC endpoint 9종 (s3·ecr.api·ecr.dkr·logs·secretsmanager·ssm·sts·monitoring·kms), Fargate `EphemeralStorage.SizeInGiB = 21`, DDB TTL 90d, task role `kms:Decrypt`가 specific CMK ARN으로 scoped, `ObjectLockEnabled=true` 부재 시 fail

### 16.3 cdk-nag
- `NagSuites.AwsSolutionsChecks`를 `App`에 부착. 모든 경고는 PR 단계에서 resolve 또는 explicit suppression with reason.

### 16.4 Integration smoke
- `cdk synth` + `cdk deploy --no-execute` (ChangeSet만) 성공을 CI에서 검증.
- `make run DESIGN=gcd STACK=orfs` 한 줄이 실제 deploy 후 통과하는지는 KG-A 역할.

### 16.5 Python test coverage
- `src/semi_design_runner/*` ≥ 85% (overview Code Conventions).
- `schemas.py`, `metrics.py`, `aws/ddb.py::put_with_count`, ValidateSpec rejection은 100% 목표.

## 부록 A — 참조

- Parent: `docs/superpowers/specs/2026-04-19-integrated-research-program-design.md` (overview)
- Canonical decision table: overview §5.3
- Layer interface contract: overview §3.2
- Lockfile spec: overview §6.2 (**본 spec §9와 필드명 정합**)
- Kill gates: overview §8 G1
- K1 constraints: `docs/knowledge-base/2026-04-19-k1-direction-report.md`

## 부록 B — Codex L1 리뷰 반영 tracking

| # | Severity | Codex 요지 | 반영 위치 |
|---|---|---|---|
| 1 | high | `Spec.parameters: dict[str, Any]` trap | §4.1 tagged union (`FlowParameters`/`ResourceOverrides`/`ExperimentalParameters`) + `Extra.forbid` |
| 2 | high | ibex/aes rejection path 미정의 | §4.2 `RejectedNotInG1Scope` + §12 ValidateSpec 의무, plan에서 pytest로 검증 |
| 3 | medium | lockfile field drift | §9에서 `commit_shas`, `source_tarball_mirrors`로 overview 정합 |
| 4 | high | KG-B Chipyard 불필요 + cache 미정의 | §10 KG-B를 cache integrity check로 축소, G1 exit 필수 아님(§11). Chipyard 전체 빌드는 L3 readiness로 이동 |
| 5 | high | KG-C dry-run으로 quota 미검증 + secrets | §10 KG-C를 2단계(deterministic C1 + optional C2) 분할 + §13 Secrets Manager |
| 6 | high | KG-D pre-emption 메커니즘 부재 | §10 `SIMULATE_SPOT_RECLAIM` env var + container SIGTERM. Production smoke는 KG-D-prod 옵션 |
| 7 | medium | KG-E CloudWatch 귀속 불가 | §6.2 `Candidates.ddb_write_count` app-level counter, §10 script가 DDB 조회 |
| 8 | high | VPC endpoint 부족 + ephemeral storage | §6.1 endpoint 8종 명시 + Fargate `ephemeral_storage_gb: 21` default |
| 9 | medium | `_SUCCESS` / object lock 순서 | §4.3 staging → ValidateManifest → copy to final → sidecars → `_SUCCESS` → Object Lock |
| 10 | medium | Cost model 미정의 | §4.1 `planned_cost_per_stage_usd` + §7.2 `semi-run cost` + §11 budget guard + §14 $50/$100 알람 |
| 11 | medium | sim/sign-off boundary | §3 명시: "G1 sign-off clean은 functional correctness evidence가 아니다" |
| 12 | medium | Risk + CDK test 누락 | §14 리스크 7종 추가 (vCPU quota, CDK drift, ECR rate, KMS, rollback, CLI auth, log retention, secrets redaction) + §16 CDK Test Strategy 신설 |

## 부록 C — 기존 Phase 1a 재사용

- `src/semi_design_wiki/*` (wiki engine) — L1은 읽지 않는다 (L2에서 씀)
- `make install / test / lint / fmt / clean` — 기존 타겟 유지, `make run` / `make lockfile-verify` / `make kg-all` 신설
- `pyproject.toml` extras — `runner = ["boto3", "click", "ulid-py"]` 추가
