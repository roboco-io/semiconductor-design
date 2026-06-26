#!/usr/bin/env node
import "source-map-support/register";
import * as path from "path";
import * as dotenv from "dotenv";
import { App, Tags } from "aws-cdk-lib";
import { EdaFlowStack } from "../lib/eda-flow-stack";

// 계정 ID·region 등 환경별 값은 repo 루트 .env에서 주입한다(.env는 커밋되지 않음).
// 템플릿: .env.example. 자세한 절차는 cdk/DEPLOY.md.
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

const account = process.env.CDK_DEFAULT_ACCOUNT;
if (!account) {
  throw new Error(
    "CDK_DEFAULT_ACCOUNT 미설정 — repo 루트의 .env.example을 .env로 복사해 AWS 계정 ID를 채우세요.",
  );
}

const app = new App();

// roboco 계정은 다른 프로젝트와 공유 — stack 이름 prefix로 충돌 회피.
new EdaFlowStack(app, "semi-design-eda-dev", {
  env: {
    account,
    region: process.env.CDK_DEFAULT_REGION ?? "ap-northeast-2",
  },
});

Tags.of(app).add("project", "semi-design-eda");
