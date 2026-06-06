---
id: 006
title: EDA flow 실행 인프라 (실 데이터셋 생성 위치)
status: resolved
type: decision
blocks: ["FR-1 실 데이터셋", F4]
related_prd: "§8 (EDA flow plane), FR-1"
related_intent: "Not §기술제약 (오픈소스만), 범위 밖 (전체 공정 운영은 archive)"
---

# 006 — EDA flow 실행 인프라

## 배경

prepare.py의 입력(진짜 `report_checks` 2시점)을 만드는 **EDA flow를 어디서 돌릴지** 미정. 파서 검증은 로컬 Docker(arm64 + amd64 QEMU emulation)로 했으나, **F4: QEMU가 CTS/route를 illegal instruction으로 실행 못 함** → 진짜 post-route label 로컬 확보 불가 (`experiments/real-gcd/FINDINGS.md`).

학습 루프(train.py 후보)는 PRD §8에서 **SageMaker Spot**으로 별도 plane. 본 issue는 그와 독립인 **EDA flow(데이터 생성) plane**의 위치 결정.

## 옵션

- **A. ECS Fargate (Operator 제안, 유력)** — native x86 실행이라 QEMU emulation 부재 → CTS/route 완주(F4 해결). Spot로 다수 설계·구성 병렬. **archive prior-art 재사용**: `cdk/WorkflowStack.ts`, `docker/orfs-runner.Dockerfile`(RUN_ID/STAGE/INPUT_S3_URI 등 env 계약), `docker/build-orfs.sh`. 단 ECR push·S3 artifact·IAM 셋업 필요.
- **B. AWS Batch** — 동일 native x86 + 큐. EDA 배치에 흔하나 archive prior-art는 Fargate.
- **C. 로컬 native x86 머신** — emulation 회피하나 병렬·확장성 낮음, Operator 머신 의존.
- **D. 로컬 Docker 유지(emulation)** — F4로 진짜 post-route 불가. 파서/F3 설계 검증까지만 가능.

## 결정 기준

- F4 해결(native x86)이 필수 — 진짜 post-route label 없으면 surrogate label이 placeholder.
- 재현성: `flow_lockfile_sha` 앵커 위해 SHA-pinned 이미지(archive orfs-runner) 재사용.
- 비용 vs 병렬성: Spot로 다수 flow 병렬 시 데이터 규모(OD-3) 경험 확정 가속.
- 셋업 비용: archive CDK/Docker 복원 노력.

## 액션 아이템

- [ ] A(Fargate) vs B(Batch) 확정.
- [ ] archive `cdk/` + `docker/orfs-runner.Dockerfile` 복원·갱신(SHA pin).
- [ ] ECR/S3/IAM 최소 셋업.
- [ ] gcd 1회 native 실행으로 **진짜 post-route** report_checks 확보 → `experiments/real-gcd/` 갱신, F4 종결.

> 본 issue는 **실 데이터셋 단계**에서 닫는다. F3(두-시점 pairing 설계)·파서 F1/F2 수정은 본 issue와 독립으로 선행 가능.

## 설계 확정 (2026-06-06, brainstorming)

옵션 A(Fargate) 채택. **최소 one-shot** 구성 + **최소 CDK 스택 1개**로 결정. AWS 프로필 `roboco`(account 779411790546), region us-east-1. 설계: `docs/superpowers/specs/2026-06-06-eda-flow-fargate-oneshot-design.md`.

- prebuilt `openroad/orfs@sha256:<digest>` native x86 Fargate task → ORFS gcd 완주(F4 해결) → 두-시점 minimal `report_checks` → S3.
- `EdaFlowStack`(ECR·S3·IAM·ECS·TaskDef·LogGroup). Step Functions/DynamoDB/batch는 YAGNI(후속).
- digest-pin으로 재현성(NFR-2). 실제 `cdk deploy`/`run-task`는 **Operator 확인 후**(비용).

status는 **실제 배포 + 진짜 post-route 리포트 S3 적재 후** resolved.

## Resolution (2026-06-06, 실제 배포 + 검증)

✅ **배포·실행·검증 완료.** native x86 ECS Fargate(`semi-design-eda-dev`, ap-northeast-2)에서 ORFS gcd 완주(CTS/route 성공, **F4 해결**) → 진짜 두-시점 report_checks → S3 → **prepare.py 파싱 n_samples=53**. F1(두-줄 헤더)·F3(endpoint join) 실데이터 검증. 5회 deploy iteration(env.sh/argv/awscli v2/stdout redirect)으로 EDA-flow 문제 수렴. 상세: `experiments/real-gcd-fargate/VALIDATION.md`. region은 roboco 프로필 기본값 ap-northeast-2로 정정.

인프라는 idle 비용 ~0(Fargate는 run당 과금)이라 다설계 batch(OD-3)용으로 유지 가능. teardown은 `cdk/DEPLOY.md` step 6.
