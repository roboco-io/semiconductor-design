#!/usr/bin/env node
import "source-map-support/register";
import { App, Tags } from "aws-cdk-lib";
import { EdaFlowStack } from "../lib/eda-flow-stack";

const app = new App();

// roboco 계정(779411790546)은 다른 프로젝트와 공유 — stack 이름 prefix로 충돌 회피.
new EdaFlowStack(app, "semi-design-eda-dev", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
});

Tags.of(app).add("project", "semi-design-eda");
