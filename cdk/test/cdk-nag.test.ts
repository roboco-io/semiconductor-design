import { Annotations, Match, Template } from "aws-cdk-lib/assertions";
import { Stack } from "aws-cdk-lib";
import { buildApp } from "../bin/semi-design";

describe("cdk-nag AwsSolutionsChecks", () => {
  const app = buildApp({ env: "dev" });
  app.synth();

  // Stack ids are prefixed with `semi-design-${env}-` in bin/semi-design.ts
  // to avoid CloudFormation collisions when this app is deployed alongside
  // other projects in the same AWS account (e.g. Roboco 779411790546 already
  // hosts a 'serverless-openclaw' project with bare StorageStack / NetworkStack).
  const stackIds = [
    "semi-design-dev-NetworkStack",
    "semi-design-dev-StorageStack",
    "semi-design-dev-ContainerStack",
    "semi-design-dev-ComputeStack",
    "semi-design-dev-WorkflowStack",
    "semi-design-dev-ObservabilityStack",
  ];

  it("composes the expected 6 stacks at the App root", () => {
    for (const stackName of stackIds) {
      expect(app.node.tryFindChild(stackName)).toBeDefined();
    }
  });

  it("has zero unsuppressed Error-level cdk-nag findings on each stack", () => {
    for (const stackName of stackIds) {
      const stack = app.node.tryFindChild(stackName) as Stack | undefined;
      if (!stack) continue;
      const errors = Annotations.fromStack(stack).findError(
        "*",
        Match.stringLikeRegexp("AwsSolutions-.*"),
      );
      expect({ stack: stackName, errors }).toEqual({ stack: stackName, errors: [] });
    }
  });

  it("Fargate TaskDefinitions declare EphemeralStorage.SizeInGiB=21 (load-bearing § ephemeral)", () => {
    const compute = app.node.tryFindChild("semi-design-dev-ComputeStack") as Stack;
    expect(compute).toBeDefined();
    const tmpl = Template.fromStack(compute).toJSON();
    const tds = Object.values(
      tmpl.Resources as Record<string, { Type: string; Properties: unknown }>,
    ).filter((r) => r.Type === "AWS::ECS::TaskDefinition");
    expect(tds.length).toBeGreaterThanOrEqual(3);
    for (const td of tds) {
      const props = td.Properties as { EphemeralStorage?: { SizeInGiB?: number } };
      expect(props.EphemeralStorage?.SizeInGiB).toBe(21);
    }
  });

  it("task role kms:Decrypt binds to specific CMK ARN, never '*'", () => {
    const compute = app.node.tryFindChild("semi-design-dev-ComputeStack") as Stack;
    const tmpl = Template.fromStack(compute).toJSON();
    const policies = Object.values(
      tmpl.Resources as Record<string, { Type: string; Properties: unknown }>,
    ).filter((r) => r.Type === "AWS::IAM::Policy");
    for (const pol of policies) {
      const stmts = (pol.Properties as { PolicyDocument: { Statement: unknown[] } }).PolicyDocument
        .Statement;
      for (const stmt of stmts as Array<{ Action?: string | string[]; Resource?: unknown }>) {
        const acts = Array.isArray(stmt.Action) ? stmt.Action : [stmt.Action];
        if (!acts.includes("kms:Decrypt")) continue;
        const resArr = Array.isArray(stmt.Resource) ? stmt.Resource : [stmt.Resource];
        for (const r of resArr) {
          expect(r).not.toBe("*");
        }
      }
    }
  });

  it("Events DynamoDB TTL is enabled on attribute 'ttl'", () => {
    const storage = app.node.tryFindChild("semi-design-dev-StorageStack") as Stack;
    const tmpl = Template.fromStack(storage).toJSON();
    const tables = Object.values(
      tmpl.Resources as Record<string, { Type: string; Properties: unknown }>,
    ).filter((r) => r.Type === "AWS::DynamoDB::Table");
    const events = tables.find((t) => {
      const name = (t.Properties as { TableName?: string }).TableName;
      return typeof name === "string" && name.includes("Events");
    });
    expect(events).toBeDefined();
    expect(
      (
        events!.Properties as {
          TimeToLiveSpecification?: { Enabled: boolean; AttributeName: string };
        }
      ).TimeToLiveSpecification,
    ).toEqual({ Enabled: true, AttributeName: "ttl" });
  });
});
