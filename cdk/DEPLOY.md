# EdaFlow 배포 런북 (Operator 전용 — 비용 발생)

> 계정 ID·region은 repo 루트 `.env`에서 주입한다(`.env.example` 참조 — `.env`는 커밋되지 않음).
> 모든 명령은 `--profile $AWS_PROFILE`. 실행 전 Operator 확인 필수. 완료 후 `cdk destroy`로 비용 정리.

## 0. 환경 로드 (셸 세션마다 1회)
    cd cdk
    set -a; source ../.env; set +a   # CDK_DEFAULT_ACCOUNT / CDK_DEFAULT_REGION / AWS_PROFILE 주입
    # 이후 cdk 명령은 eda-flow.ts가 .env를 자동 로드(dotenv)하지만,
    # aws CLI 명령에도 같은 값이 필요하므로 셸에 source 해 둔다.

## 1. Bootstrap (최초 1회)
    npm install
    npx cdk bootstrap --profile "$AWS_PROFILE"

## 2. Deploy 스택
    npx cdk deploy --profile "$AWS_PROFILE" --require-approval any-change
    # 출력(CfnOutput): RepoUri, BucketName, ClusterArn, TaskDefArn, PublicSubnet

## 3. Runner 이미지 build+push (ECR)
    aws ecr get-login-password --region "$CDK_DEFAULT_REGION" --profile "$AWS_PROFILE" \
      | docker login --username AWS --password-stdin "$CDK_DEFAULT_ACCOUNT.dkr.ecr.$CDK_DEFAULT_REGION.amazonaws.com"
    docker build --platform linux/amd64 -t <REPO_URI>:latest -f docker/eda-flow-runner.Dockerfile docker/
    docker push <REPO_URI>:latest

## 4. run-task (one-shot)
    aws ecs run-task --cluster <CLUSTER> --task-definition <TASKDEF> \
      --launch-type FARGATE --region "$CDK_DEFAULT_REGION" --profile "$AWS_PROFILE" \
      --network-configuration 'awsvpcConfiguration={subnets=[<PUBLIC_SUBNET>],assignPublicIp=ENABLED}'
    # CloudWatch 로그(/eda-flow)에서 진행 확인. 완료까지 수 분.

## 5. 리포트 회수 + 파서 검증
    aws s3 cp --recursive s3://<BUCKET>/runs/gcd/<RUN_ID>/ experiments/real-gcd-fargate/ --profile "$AWS_PROFILE"
    uv run python prepare.py --synth experiments/real-gcd-fargate/synth.rpt \
      --route experiments/real-gcd-fargate/route.rpt \
      --lockfile experiments/real-gcd-fargate/versions.txt --design-id gcd --out-dir /tmp/realds
    # n_samples > 0 이면 F4 종결 + 실데이터 파이프 검증 성공.

## 6. 정리
    npx cdk destroy --profile "$AWS_PROFILE"
