import { Aspects } from "aws-cdk-lib";
import { AwsSolutionsChecks } from "cdk-nag";
import { buildApp } from "../bin/semi-design";

describe("App bootstrap", () => {
  it("synthesizes 6 stacks and attaches cdk-nag AwsSolutionsChecks", () => {
    const app = buildApp({ env: "dev" });
    // cdk-nag aspect must be attached at construction; test proves the hook is live.
    const aspects = Aspects.of(app).all;
    expect(aspects.some((a) => a instanceof AwsSolutionsChecks)).toBe(true);
    // App.synth() succeeds with all 6 stacks composed.
    const cloudAssembly = app.synth();
    expect(cloudAssembly.stacks.length).toBe(6);
    const stackNames = cloudAssembly.stacks.map((s) => s.stackName).sort();
    expect(stackNames).toEqual([
      "semi-design-dev-ComputeStack",
      "semi-design-dev-ContainerStack",
      "semi-design-dev-NetworkStack",
      "semi-design-dev-ObservabilityStack",
      "semi-design-dev-StorageStack",
      "semi-design-dev-WorkflowStack",
    ]);
  });

  it("rejects unknown context env value", () => {
    expect(() => buildApp({ env: "staging" as "dev" | "prod" })).toThrow(
      /env must be 'dev' or 'prod'/,
    );
  });
});
