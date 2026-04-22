import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";

describe("ComputeStack", () => {
  const app = new App({ context: { env: "dev" } });
  const network = new NetworkStack(app, "NetworkTest", { env: "dev" });
  const storage = new StorageStack(app, "StorageTest", { env: "dev" });
  const container = new ContainerStack(app, "ContainerTest", { env: "dev" });
  const compute = new ComputeStack(app, "ComputeTest", {
    env: "dev",
    vpc: network.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const template = Template.fromStack(compute);

  it("creates an ECS cluster with no EC2 capacity", () => {
    template.resourceCountIs("AWS::ECS::Cluster", 1);
    template.resourceCountIs("AWS::AutoScaling::AutoScalingGroup", 0);
  });

  it("creates 4 Fargate TaskDefinitions (3 runtime + kg-c2-smoke) with EphemeralStorage.SizeInGiB=21", () => {
    template.resourceCountIs("AWS::ECS::TaskDefinition", 4);
    const tds = template.findResources("AWS::ECS::TaskDefinition", {
      Properties: {
        EphemeralStorage: { SizeInGiB: 21 },
      },
    });
    expect(Object.keys(tds).length).toBe(4);
  });

  it("task role kms:Decrypt is scoped to specific CMK ARNs, never '*'", () => {
    const policies = template.findResources("AWS::IAM::Policy");
    for (const [, res] of Object.entries(policies)) {
      const stmts = (
        res as { Properties: { PolicyDocument: { Statement: unknown[] } } }
      ).Properties.PolicyDocument.Statement;
      for (const stmt of stmts as Array<{
        Action?: string | string[];
        Resource?: unknown;
      }>) {
        const actions = Array.isArray(stmt.Action)
          ? stmt.Action
          : [stmt.Action];
        if (actions.includes("kms:Decrypt")) {
          expect(stmt.Resource).toBeDefined();
          expect(stmt.Resource).not.toBe("*");
          const resArr = Array.isArray(stmt.Resource)
            ? stmt.Resource
            : [stmt.Resource];
          for (const r of resArr) {
            expect(r).not.toBe("*");
          }
        }
      }
    }
  });

  it("only the kg-c2-smoke task role has secretsmanager:GetSecretValue", () => {
    const secretsAllowers = Object.entries(
      template.findResources("AWS::IAM::Policy"),
    ).filter(([, res]) => {
      const stmts = (
        res as { Properties: { PolicyDocument: { Statement: unknown[] } } }
      ).Properties.PolicyDocument.Statement;
      return (stmts as Array<{ Action?: string | string[] }>).some((s) => {
        const actions = Array.isArray(s.Action) ? s.Action : [s.Action];
        return actions.includes("secretsmanager:GetSecretValue");
      });
    });
    expect(secretsAllowers.length).toBe(1);
  });

  it("exposes kg-c2-smoke TaskDefinition for KG-C2 Fargate execution", () => {
    expect(compute.kgC2SmokeTaskDef).toBeDefined();
    template.hasResourceProperties("AWS::ECS::TaskDefinition", {
      Family: Match.stringLikeRegexp("kg-c2-smoke"),
    });
  });

  it("exposes 3 runtime TaskDefinitions as public properties", () => {
    expect(compute.orfsRunnerTaskDef).toBeDefined();
    expect(compute.librelaneRunnerTaskDef).toBeDefined();
    expect(compute.metricCollectorTaskDef).toBeDefined();
  });
});
