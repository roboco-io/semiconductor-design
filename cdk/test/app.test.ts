import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { AwsSolutionsChecks } from "cdk-nag";
import { Aspects } from "aws-cdk-lib";
import { buildApp } from "../bin/semi-design";

describe("App bootstrap", () => {
  it("synthesizes with no stacks yet and attaches cdk-nag AwsSolutionsChecks", () => {
    const app = buildApp({ env: "dev" });
    // cdk-nag aspect must be attached at construction; test proves the hook is live.
    const aspects = Aspects.of(app).all;
    expect(aspects.some((a) => a instanceof AwsSolutionsChecks)).toBe(true);
    // App.synth() must succeed even with zero stacks (pre-Task B2 state).
    const cloudAssembly = app.synth();
    expect(cloudAssembly.stacks.length).toBe(0);
  });

  it("rejects unknown context env value", () => {
    expect(() => buildApp({ env: "staging" as "dev" | "prod" })).toThrow(
      /env must be 'dev' or 'prod'/,
    );
  });
});
