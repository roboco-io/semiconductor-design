# EDA Flow Fargate One-shot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`).

**Goal:** Build the infra CODE for a minimal one-shot Fargate run that executes ORFS gcd natively (x86, no emulation) and uploads two-stage `report_checks` to S3 — verified by `cdk synth` + jest with **no AWS deploy** (deploy is Operator-gated).

**Architecture:** One CDK stack `EdaFlowStack` (ECR, S3, IAM exec+task, ECS Fargate cluster, TaskDefinition, LogGroup) + a thin runner image (`FROM openroad/orfs@sha256:…` + awscli + entrypoint + Tcl). All deploy/run/build-push steps documented in `cdk/DEPLOY.md` for the Operator to execute after confirmation.

**Tech Stack:** AWS CDK 2.140 (TypeScript), jest+ts-jest, Docker, bash, OpenSTA Tcl. Node/npm.

**Spec:** `docs/superpowers/specs/2026-06-06-eda-flow-fargate-oneshot-design.md`. **Gate:** no `cdk deploy`, no image build/push, no `run-task` — those go in DEPLOY.md only.

---

## Files

| File | Responsibility |
|---|---|
| `cdk/package.json`,`cdk/tsconfig.json`,`cdk/cdk.json`,`cdk/jest.config.js` | CDK project config |
| `cdk/bin/eda-flow.ts` | CDK App entry (stack-name prefix `semi-design-eda-`) |
| `cdk/lib/eda-flow-stack.ts` | the single stack |
| `cdk/test/eda-flow-stack.test.ts` | jest synth assertions |
| `docker/eda-flow-runner.Dockerfile` | thin runner image (digest-pinned base) |
| `docker/eda-flow/entrypoint.sh` | run ORFS gcd → dump reports → s3 cp |
| `docker/eda-flow/dump_report_checks.tcl` | minimal report_checks per stage |
| `cdk/DEPLOY.md` | Operator-gated deploy runbook |

Verification spends NO money: `cd cdk && npm install && npm test && npx cdk synth` (synth is local, no AWS calls). Docker/shell/Tcl are authored + reviewed; executed only at Operator-gated deploy.

---

### Task 1: CDK project scaffolding

**Files:** Create `cdk/package.json`, `cdk/tsconfig.json`, `cdk/cdk.json`, `cdk/jest.config.js`, `cdk/.gitignore`

- [ ] **Step 1: Create `cdk/package.json`**

```json
{
  "name": "semi-design-eda-cdk",
  "version": "0.1.0",
  "private": true,
  "bin": { "eda-flow": "bin/eda-flow.js" },
  "scripts": { "build": "tsc", "test": "jest", "cdk": "cdk" },
  "devDependencies": {
    "@types/jest": "^29.5.12",
    "@types/node": "^20.11.30",
    "aws-cdk": "^2.140.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.2",
    "ts-node": "^10.9.2",
    "typescript": "^5.4.5"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.140.0",
    "constructs": "^10.3.0",
    "source-map-support": "^0.5.21"
  }
}
```

- [ ] **Step 2: Create `cdk/cdk.json`**

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/eda-flow.ts",
  "context": { "env": "dev" }
}
```

- [ ] **Step 3: Create `cdk/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["es2020"],
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": ["node", "jest"]
  },
  "exclude": ["node_modules", "cdk.out"]
}
```

- [ ] **Step 4: Create `cdk/jest.config.js`**

```js
module.exports = {
  testEnvironment: "node",
  roots: ["<rootDir>/test"],
  testMatch: ["**/*.test.ts"],
  transform: { "^.+\\.tsx?$": "ts-jest" },
};
```

- [ ] **Step 5: Create `cdk/.gitignore`**

```
node_modules
cdk.out
*.js
*.d.ts
```

- [ ] **Step 6: Install + commit**

Run: `cd cdk && npm install`
Expected: dependencies install, no fatal error.

```bash
git add cdk/package.json cdk/tsconfig.json cdk/cdk.json cdk/jest.config.js cdk/.gitignore cdk/package-lock.json
git commit -m "build(cdk): EdaFlow CDK 프로젝트 scaffolding"
```

---

### Task 2: `EdaFlowStack`

**Files:** Create `cdk/lib/eda-flow-stack.ts`

- [ ] **Step 1: Write a failing test** (`cdk/test/eda-flow-stack.test.ts`)

```typescript
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { EdaFlowStack } from "../lib/eda-flow-stack";

function synth() {
  const app = new App();
  const stack = new EdaFlowStack(app, "semi-design-eda-dev", { env: { account: "111111111111", region: "us-east-1" } });
  return Template.fromStack(stack);
}

test("provisions an S3 artifact bucket", () => {
  synth().resourceCountIs("AWS::S3::Bucket", 1);
});

test("provisions an ECR repository", () => {
  synth().resourceCountIs("AWS::ECR::Repository", 1);
});

test("provisions a Fargate task definition with awslogs + a log group", () => {
  const t = synth();
  t.resourceCountIs("AWS::ECS::TaskDefinition", 1);
  t.resourceCountIs("AWS::Logs::LogGroup", 1);
  t.hasResourceProperties("AWS::ECS::TaskDefinition", {
    RequiresCompatibilities: ["FARGATE"],
    Cpu: "4096",
    Memory: "16384",
  });
});

test("task role can write to the artifact bucket", () => {
  // S3 put permission present on some IAM policy
  synth().hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({ Action: Match.arrayWith(["s3:PutObject"]) }),
      ]),
    },
  });
});
```

Add `import { Match } from "aws-cdk-lib/assertions";` at the top.

- [ ] **Step 2: Run to verify it fails**

Run: `cd cdk && npm test`
Expected: FAIL — `../lib/eda-flow-stack` not found.

- [ ] **Step 3: Implement `cdk/lib/eda-flow-stack.ts`**

```typescript
import { Stack, StackProps, RemovalPolicy, Duration } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as logs from "aws-cdk-lib/aws-logs";

/**
 * 최소 one-shot Fargate EDA flow 스택.
 * ORFS gcd를 native x86로 완주 → 두-시점 report_checks → S3.
 * Step Functions/DynamoDB/batch는 YAGNI (후속). on-demand only.
 */
export class EdaFlowStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const artifacts = new s3.Bucket(this, "Artifacts", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const repo = new ecr.Repository(this, "RunnerRepo", {
      imageScanOnPush: true,
      removalPolicy: RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    const logGroup = new logs.LogGroup(this, "RunnerLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // default VPC 사용 (NAT 없는 public subnet + assignPublicIp).
    const vpc = ec2.Vpc.fromLookup(this, "DefaultVpc", { isDefault: true });
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });

    const taskDef = new ecs.FargateTaskDefinition(this, "RunnerTask", {
      cpu: 4096,
      memoryLimitMiB: 16384,
      ephemeralStorageGiB: 50,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    artifacts.grantWrite(taskDef.taskRole);

    taskDef.addContainer("runner", {
      image: ecs.ContainerImage.fromEcrRepository(repo, "latest"),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "eda-flow", logGroup }),
      environment: { ARTIFACT_BUCKET: artifacts.bucketName, DESIGN: "gcd" },
    });
  }
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd cdk && npm test`
Expected: PASS (4 tests). (`Vpc.fromLookup` returns a dummy VPC under test context — if it errors, the test env account/region are set in the test, which CDK uses for the dummy lookup.)

- [ ] **Step 5: Commit**

```bash
git add cdk/lib/eda-flow-stack.ts cdk/test/eda-flow-stack.test.ts
git commit -m "feat(cdk): EdaFlowStack — ECR·S3·IAM·ECS Fargate taskdef·LogGroup"
```

---

### Task 3: CDK App entry + synth

**Files:** Create `cdk/bin/eda-flow.ts`

- [ ] **Step 1: Implement `cdk/bin/eda-flow.ts`**

```typescript
#!/usr/bin/env node
import "source-map-support/register";
import { App, Tags } from "aws-cdk-lib";
import { EdaFlowStack } from "../lib/eda-flow-stack";

const app = new App();

// roboco 계정(AWS_ACCOUNT_ID)은 다른 프로젝트와 공유 — stack 이름 prefix로 충돌 회피.
new EdaFlowStack(app, "semi-design-eda-dev", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
});

Tags.of(app).add("project", "semi-design-eda");
```

- [ ] **Step 2: Verify synth succeeds (no AWS deploy)**

Run: `cd cdk && CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 npx cdk synth --quiet`
Expected: synth prints the template (or writes cdk.out) with no error. (Dummy account avoids the real `Vpc.fromLookup`; CDK uses a stub VPC for synth with explicit env.)

- [ ] **Step 3: Commit**

```bash
git add cdk/bin/eda-flow.ts
git commit -m "feat(cdk): EdaFlow App entry (stack prefix semi-design-eda-)"
```

---

### Task 4: Thin runner image + scripts

**Files:** Create `docker/eda-flow-runner.Dockerfile`, `docker/eda-flow/entrypoint.sh`, `docker/eda-flow/dump_report_checks.tcl`

> These are authored + reviewed; executed only at Operator-gated deploy. NO local build (multi-GB base pull).

- [ ] **Step 1: Create `docker/eda-flow-runner.Dockerfile`**

```dockerfile
# 최소 runner: prebuilt openroad/orfs(native x86)에 awscli + 스크립트만 얹는다.
# digest-pin으로 재현성(NFR-2) — 로컬 검증과 동일 이미지.
FROM openroad/orfs@sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69

USER root
RUN apt-get update && apt-get install -y --no-install-recommends awscli \
 && rm -rf /var/lib/apt/lists/*

COPY eda-flow/entrypoint.sh /opt/eda/entrypoint.sh
COPY eda-flow/dump_report_checks.tcl /opt/eda/dump_report_checks.tcl
RUN chmod +x /opt/eda/entrypoint.sh

ENTRYPOINT ["/opt/eda/entrypoint.sh"]
```

- [ ] **Step 2: Create `docker/eda-flow/entrypoint.sh`**

```bash
#!/usr/bin/env bash
# ORFS gcd 완주 → 두-시점 report_checks 덤프 → S3 적재.
# env: ARTIFACT_BUCKET, DESIGN(=gcd), RUN_ID(optional)
set -euo pipefail

DESIGN="${DESIGN:-gcd}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
FLOW=/OpenROAD-flow-scripts/flow
WORK=/tmp/eda-out
mkdir -p "$WORK"

cd "$FLOW"
# 1) ORFS 완주 (native x86 → CTS/route 성공)
make DESIGN_CONFIG="./designs/sky130hd/${DESIGN}/config.mk"

RES="results/sky130hd/${DESIGN}/base"
SYNTH_ODB="${RES}/1_synth.odb"
ROUTE_ODB="$(ls -1 ${RES}/*_final.odb 2>/dev/null | head -1 || true)"
[ -n "$ROUTE_ODB" ] || ROUTE_ODB="$(ls -1 ${RES}/6_*.odb | tail -1)"

# 2) 두 stage report_checks (minimal 포맷, -fields 없음 → prepare.py 파서 계약)
openroad -no_init -exit -log "$WORK/synth.log" \
  -metrics "$WORK/synth.json" \
  /opt/eda/dump_report_checks.tcl "$SYNTH_ODB" "$WORK/synth.rpt"
openroad -no_init -exit -log "$WORK/route.log" \
  -metrics "$WORK/route.json" \
  /opt/eda/dump_report_checks.tcl "$ROUTE_ODB" "$WORK/route.rpt"

# 3) versions + lockfile
{ echo "design: $DESIGN"; echo "run_id: $RUN_ID";
  echo "image_digest: sha256:b19fe0a514a87aee0f97073797395c0ca489c45406b526bc75fd2038c82fdf69";
  openroad -version 2>/dev/null | head -1 | sed 's/^/openroad: /' || true;
  yosys -V 2>/dev/null | head -1 | sed 's/^/yosys: /' || true; } > "$WORK/versions.txt"

# 4) S3 적재
DEST="s3://${ARTIFACT_BUCKET}/runs/${DESIGN}/${RUN_ID}"
aws s3 cp "$WORK/synth.rpt"   "$DEST/synth.rpt"
aws s3 cp "$WORK/route.rpt"   "$DEST/route.rpt"
aws s3 cp "$WORK/versions.txt" "$DEST/versions.txt"
echo "uploaded → $DEST"
```

- [ ] **Step 3: Create `docker/eda-flow/dump_report_checks.tcl`**

```tcl
# minimal report_checks 덤프 (-fields 없음 → Delay/Time 2-col, prepare.py 파서 계약).
# 다수 max-path를 덤프하고 endpoint별 worst는 prepare.py가 dedup한다 (F3).
# 사용: openroad ... dump_report_checks.tcl <odb> <out.rpt>
set odb  [lindex $argv 0]
set out  [lindex $argv 1]
read_db $odb
set fh [open $out w]
puts $fh [report_checks -path_delay max -format full_clock_expanded -group_path_count 10000]
close $fh
```

> **DEPLOY-time 검증 필수 (핵심 리스크):** `-group_path_count` 플래그명과 `read_db`만으로 timing 환경(liberty/SDC/RC)이 갖춰지는지는 이미지 버전 의존. 배포 첫 run 후 `synth.rpt`/`route.rpt`를 prepare.py로 파싱해 path 수>0·n_samples>0 확인. 불일치 시 Tcl 조정(예: `read_sdc`, `set_propagated_clock`, ORFS의 `setRC.tcl` source).

- [ ] **Step 4: Commit**

```bash
git add docker/eda-flow-runner.Dockerfile docker/eda-flow/entrypoint.sh docker/eda-flow/dump_report_checks.tcl
git commit -m "feat(docker): EdaFlow thin runner (orfs@digest + awscli + dump Tcl)"
```

---

### Task 5: Operator deploy runbook + final verify

**Files:** Create `cdk/DEPLOY.md`

- [ ] **Step 1: Create `cdk/DEPLOY.md`**

```markdown
# EdaFlow 배포 런북 (Operator 전용 — 비용 발생)

> 모든 명령은 `--profile roboco` (account AWS_ACCOUNT_ID). region us-east-1.
> 실행 전 Operator 확인 필수. 완료 후 `cdk destroy`로 비용 정리.

## 1. Bootstrap (최초 1회)
    cd cdk && npm install
    CDK_DEFAULT_ACCOUNT=AWS_ACCOUNT_ID CDK_DEFAULT_REGION=us-east-1 \
      npx cdk bootstrap --profile roboco

## 2. Deploy 스택
    CDK_DEFAULT_ACCOUNT=AWS_ACCOUNT_ID CDK_DEFAULT_REGION=us-east-1 \
      npx cdk deploy --profile roboco --require-approval any-change
    # 출력: RunnerRepo URI, Artifacts 버킷명, Cluster/TaskDef ARN

## 3. Runner 이미지 build+push (ECR)
    AWS_PROFILE=roboco aws ecr get-login-password --region us-east-1 \
      | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.us-east-1.amazonaws.com
    docker build --platform linux/amd64 -t <REPO_URI>:latest -f docker/eda-flow-runner.Dockerfile docker/
    docker push <REPO_URI>:latest

## 4. run-task (one-shot)
    AWS_PROFILE=roboco aws ecs run-task --cluster <CLUSTER> --task-definition <TASKDEF> \
      --launch-type FARGATE --region us-east-1 \
      --network-configuration 'awsvpcConfiguration={subnets=[<PUBLIC_SUBNET>],assignPublicIp=ENABLED}'
    # CloudWatch 로그(/eda-flow)에서 진행 확인. 완료까지 수 분.

## 5. 리포트 회수 + 파서 검증
    AWS_PROFILE=roboco aws s3 cp --recursive s3://<BUCKET>/runs/gcd/<RUN_ID>/ experiments/real-gcd-fargate/
    uv run python prepare.py --synth experiments/real-gcd-fargate/synth.rpt \
      --route experiments/real-gcd-fargate/route.rpt \
      --lockfile experiments/real-gcd-fargate/versions.txt --design-id gcd --out-dir /tmp/realds
    # n_samples > 0 이면 F4 종결 + 실데이터 파이프 검증 성공.

## 6. 정리
    npx cdk destroy --profile roboco
```

- [ ] **Step 2: Final verify (no deploy)**

Run:
```bash
cd /Users/dohyunjung/Workspace/roboco-io/research/semiconductor-design/cdk
npm test
CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 npx cdk synth --quiet >/dev/null && echo "synth OK"
```
Expected: jest all pass, `synth OK`.

- [ ] **Step 3: Commit**

```bash
git add cdk/DEPLOY.md
git commit -m "docs(cdk): EdaFlow Operator 배포 런북"
```

---

## Self-Review

**Spec coverage:** EdaFlowStack ECR·S3·IAM·ECS·TaskDef·LogGroup (Task 2) · App+prefix (Task 3) · thin digest-pinned runner + entrypoint + minimal Tcl (Task 4) · deploy gated to DEPLOY.md (Task 5) · verify by synth+jest only, no deploy. YAGNI: no Step Functions/DynamoDB/observability/Spot.

**Placeholder scan:** none in code. `<ACCOUNT>/<REPO_URI>/<CLUSTER>/<TASKDEF>/<PUBLIC_SUBNET>/<RUN_ID>/<BUCKET>` in DEPLOY.md are intentional runtime values the Operator fills from deploy outputs — documented as such, not code placeholders.

**Consistency:** stack id `semi-design-eda-dev` consistent (bin + test). env vars `ARTIFACT_BUCKET`/`DESIGN` set in stack container env and consumed in entrypoint.sh. `dump_report_checks.tcl` arg order `<odb> <out>` matches entrypoint invocation. Image digest identical in Dockerfile + entrypoint versions.txt.

**Key-risk flag:** the Tcl's `-group_path_count` flag + timing-env sufficiency is the one piece not verifiable without deploy — explicitly called out in Task 4 Step 3 with a deploy-time validation procedure (parse with prepare.py, n_samples>0). Not a silent gap.
