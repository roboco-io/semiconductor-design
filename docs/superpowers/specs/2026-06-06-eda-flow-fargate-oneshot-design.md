# issue 006 — 최소 one-shot Fargate EDA flow 설계

> status: approved (2026-06-06, brainstorming) · 후속: CDK+runner writing-plans
> 근거: `experiments/real-gcd/FINDINGS.md` F4(QEMU emulation이 CTS/route 불가) + `issues/006`.
> AWS: 프로필 `roboco` (account AWS_ACCOUNT_ID), region us-east-1(default).
> **배포 게이트**: 실제 `cdk deploy`/`run-task`는 비용·외부 영향이라 plan 승인 + Operator 확인 후. 코드·`cdk synth`·테스트까지만 자율.

## 1. 목표 (범위)

단일 Fargate task가 **native x86**로 ORFS gcd flow를 완주(emulation 없음 → CTS/route 성공 = F4 해결) → **두-시점 `report_checks`(post-synth + post-route)를 minimal 포맷으로 S3에** 적재. prepare→train 전 파이프를 실데이터로 1회 통과. 다설계 batch는 후속(YAGNI).

## 2. 구성

```
[thin runner image → ECR]  FROM openroad/orfs@sha256:<digest>
   + awscli + entrypoint.sh + dump_report_checks.tcl
        │  ECS Fargate run-task (x86_64, on-demand, default VPC public subnet + assignPublicIp)
        ▼
[EdaFlowStack (CDK 1개, TypeScript)]
   ECR repo · S3 bucket · IAM(execution+task) · ECS Fargate cluster · TaskDefinition · CloudWatch LogGroup
        │
        ▼
[S3]  s3://<bucket>/runs/<design>/<run_id>/{synth.rpt, route.rpt, versions.txt, lockfile.yaml}
```

## 3. 컨테이너 동작 (entrypoint.sh)

1. ORFS `make DESIGN_CONFIG=./designs/sky130hd/gcd/config.mk` **완주**(synth→floorplan→place→CTS→route).
2. `openroad -no_init -exit dump_report_checks.tcl` 를 두 stage에 — `1_synth.odb`(post-synth) + 최종 routed odb(post-route, 예: `6_final.odb`).
3. 각 stage: **minimal `report_checks`** (no `-fields` → Delay/Time 2-col) + **endpoint별 worst max-delay path**. prepare.py F1 파서(두-줄 헤더)·F3 endpoint join과 정합.
4. `openroad -version`/`yosys -V` → `versions.txt`; 이미지 digest 기록. `aws s3 cp`로 리포트·versions·lockfile → S3.

## 4. 재현성 (NFR-2 정합)

`openroad/orfs`를 **digest pin**(`@sha256:<digest>`) + `versions.txt`에 도구 버전 → `DATASET.flow_lockfile_sha`가 이미지 digest+lockfile을 앵커. prebuilt이지만 digest-pin으로 재현 확보(OR-Tools 소스빌드 불요).

## 5. 비용·안전

- on-demand 단일 task(gcd 수 분), 완료 시 자동 종료. NAT 없음(public subnet + assignPublicIp). LogGroup retention 짧게(예: 1주).
- region us-east-1 default. Fargate task size: 4 vCPU / 8–16 GB(ORFS gcd 여유), ephemeral storage 30–50 GiB.
- 실제 배포는 §0 게이트.

## 6. 핵심 리스크

`dump_report_checks.tcl`의 **endpoint별 worst max-path 열거 + minimal 포맷** 정확성 — 로컬 검증에서 `-fields`로 틀렸던 지점. 정확한 OpenSTA 플래그(endpoint별 1 path)는 구현 시 grep/문서 검증(추측 금지). minimal 포맷(no -fields)이 prepare.py 파서 계약.

## 7. 컴포넌트 단위 (isolation)

| 단위 | 책임 | 검증(배포 없이) |
|---|---|---|
| `cdk/lib/eda-flow-stack.ts` | ECR·S3·IAM·ECS·TaskDef·LogGroup | `cdk synth` + jest assertion |
| `docker/eda-flow-runner.Dockerfile` | FROM orfs@digest + awscli + scripts | hadolint(있으면)/문법 |
| `docker/eda-flow/entrypoint.sh` | flow 실행 → dump → s3 cp | shellcheck(있으면) |
| `docker/eda-flow/dump_report_checks.tcl` | 두 stage minimal report_checks | 리뷰(실행은 배포 시) |

## 8. 비목표 (YAGNI)

Step Functions Map·DynamoDB·다설계 batch·full observability — 후속(batch 확장 시 archive `WorkflowStack` 재사용). on-demand만(Spot은 batch 단계).
