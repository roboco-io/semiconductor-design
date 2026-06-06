# EdaFlow 배포 런북 (Operator 전용 — 비용 발생)

> 모든 명령은 `--profile roboco` (account 779411790546). region us-east-1.
> 실행 전 Operator 확인 필수. 완료 후 `cdk destroy`로 비용 정리.

## 1. Bootstrap (최초 1회)
    cd cdk && npm install
    CDK_DEFAULT_ACCOUNT=779411790546 CDK_DEFAULT_REGION=us-east-1 \
      npx cdk bootstrap --profile roboco

## 2. Deploy 스택
    CDK_DEFAULT_ACCOUNT=779411790546 CDK_DEFAULT_REGION=us-east-1 \
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
