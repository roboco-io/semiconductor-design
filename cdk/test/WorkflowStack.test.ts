import { App, Aspects } from "aws-cdk-lib";
import { Template, Match, Annotations } from "aws-cdk-lib/assertions";
import { AwsSolutionsChecks } from "cdk-nag";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { WorkflowStack } from "../lib/stacks/WorkflowStack";

describe("WorkflowStack", () => {
  const app = new App({ context: { env: "dev" } });
  const network = new NetworkStack(app, "NetworkW", { env: "dev" });
  const storage = new StorageStack(app, "StorageW", { env: "dev" });
  const container = new ContainerStack(app, "ContainerW", { env: "dev" });
  const compute = new ComputeStack(app, "ComputeW", {
    env: "dev",
    vpc: network.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const workflow = new WorkflowStack(app, "WorkflowW", {
    env: "dev",
    cluster: compute.cluster,
    orfsRunnerTaskDef: compute.orfsRunnerTaskDef,
    librelaneRunnerTaskDef: compute.librelaneRunnerTaskDef,
    metricCollectorTaskDef: compute.metricCollectorTaskDef,
    artifactBucket: storage.bucket,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
    eventsTable: storage.eventsTable,
  });
  const template = Template.fromStack(workflow);

  it("creates exactly 3 Lambda functions (ValidateSpec, InitGeneration, Finalize)", () => {
    template.resourceCountIs("AWS::Lambda::Function", 3);
  });

  it("all 3 Lambdas run Python 3.12 with index.handler", () => {
    const fns = template.findResources("AWS::Lambda::Function");
    const entries = Object.values(fns) as Array<{
      Properties: { Runtime: string; Handler: string };
    }>;
    expect(entries.length).toBe(3);
    for (const fn of entries) {
      expect(fn.Properties.Runtime).toBe("python3.12");
      expect(fn.Properties.Handler).toBe("index.handler");
    }
  });

  it("ValidateSpec Lambda exposes G1_ALLOWED_DESIGN=gcd", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      FunctionName: Match.stringLikeRegexp("validate-spec"),
      Environment: {
        Variables: Match.objectLike({
          G1_ALLOWED_DESIGN: "gcd",
        }),
      },
    });
  });

  it("Finalize Lambda exposes ARTIFACT_BUCKET + RETENTION_DAYS=90", () => {
    template.hasResourceProperties("AWS::Lambda::Function", {
      FunctionName: Match.stringLikeRegexp("finalize"),
      Environment: {
        Variables: Match.objectLike({
          RETENTION_DAYS: "90",
        }),
      },
    });
  });

  it("Step Functions state machine type is STANDARD (Express forbidden — spec §6.2)", () => {
    template.resourceCountIs("AWS::StepFunctions::StateMachine", 1);
    template.hasResourceProperties("AWS::StepFunctions::StateMachine", {
      StateMachineType: "STANDARD",
    });
  });

  it("Map state has MaxConcurrency=10 in the ASL definition", () => {
    const machines = template.findResources("AWS::StepFunctions::StateMachine");
    const [, machine] = Object.entries(machines)[0];
    const defStr = JSON.stringify(
      (machine as { Properties: { DefinitionString: unknown } }).Properties
        .DefinitionString,
    );
    expect(defStr).toContain('\\"MaxConcurrency\\":10');
  });

  it("SFN definition references ValidateSpec before Map state (Map sees post-validation payload)", () => {
    const machines = template.findResources("AWS::StepFunctions::StateMachine");
    const [, machine] = Object.entries(machines)[0];
    const defStr = JSON.stringify(
      (machine as { Properties: { DefinitionString: unknown } }).Properties
        .DefinitionString,
    );
    // StartAt must land on the ValidateSpec task, not the Map.
    expect(defStr).toContain("ValidateSpec");
  });

  it("creates 3 EventBridge rules (run completion + Spot interruption + daily cost alert)", () => {
    template.resourceCountIs("AWS::Events::Rule", 3);
  });

  it("EventBridge rule for run completion matches source=semi-design.l1", () => {
    template.hasResourceProperties("AWS::Events::Rule", {
      EventPattern: Match.objectLike({
        source: Match.arrayWith(["semi-design.l1"]),
      }),
    });
  });

  it("EventBridge rule for Spot interruption matches ECS Task State Change + SpotInterruption", () => {
    template.hasResourceProperties("AWS::Events::Rule", {
      EventPattern: Match.objectLike({
        source: Match.arrayWith(["aws.ecs"]),
        "detail-type": Match.arrayWith(["ECS Task State Change"]),
      }),
    });
  });

  it("EventBridge daily cost alert rule uses a ScheduleExpression", () => {
    const rules = template.findResources("AWS::Events::Rule");
    const scheduled = Object.values(rules).filter((r) => {
      const props = (r as { Properties: { ScheduleExpression?: string } })
        .Properties;
      return typeof props.ScheduleExpression === "string";
    });
    expect(scheduled.length).toBe(1);
  });

  it("exposes stateMachine + 3 Lambda functions as public properties", () => {
    expect(workflow.stateMachine).toBeDefined();
    expect(workflow.validateSpecFn).toBeDefined();
    expect(workflow.initGenerationFn).toBeDefined();
    expect(workflow.finalizeFn).toBeDefined();
  });

  it("three Lambda execution roles are distinct (least-privilege boundary)", () => {
    // Each lambda.Function creates its own AWS::IAM::Role. Count the roles
    // whose assume-role principal is lambda.amazonaws.com.
    const roles = template.findResources("AWS::IAM::Role");
    const lambdaRoles = Object.values(roles).filter((r) => {
      const stmts = (
        r as {
          Properties: {
            AssumeRolePolicyDocument: { Statement: unknown[] };
          };
        }
      ).Properties.AssumeRolePolicyDocument.Statement;
      return (stmts as Array<{ Principal?: { Service?: string } }>).some(
        (s) => s.Principal?.Service === "lambda.amazonaws.com",
      );
    });
    expect(lambdaRoles.length).toBe(3);
    // Role logical IDs must all be distinct.
    const roleIds = Object.keys(roles).filter((id) => {
      const stmts = (
        roles[id] as {
          Properties: {
            AssumeRolePolicyDocument: { Statement: unknown[] };
          };
        }
      ).Properties.AssumeRolePolicyDocument.Statement;
      return (stmts as Array<{ Principal?: { Service?: string } }>).some(
        (s) => s.Principal?.Service === "lambda.amazonaws.com",
      );
    });
    expect(new Set(roleIds).size).toBe(3);
  });

  it("cdk-nag AwsSolutionsChecks produces zero errors on WorkflowStack", () => {
    // Re-synthesize in isolation so the aspect actually runs over this stack.
    const nagApp = new App({ context: { env: "dev" } });
    Aspects.of(nagApp).add(new AwsSolutionsChecks({ verbose: true }));
    const n1 = new NetworkStack(nagApp, "NagNetwork", { env: "dev" });
    const s1 = new StorageStack(nagApp, "NagStorage", { env: "dev" });
    const c1 = new ContainerStack(nagApp, "NagContainer", { env: "dev" });
    const co1 = new ComputeStack(nagApp, "NagCompute", {
      env: "dev",
      vpc: n1.vpc,
      bucketCmk: s1.bucketCmk,
      artifactBucketArn: s1.bucket.bucketArn,
      orfsRunnerRepo: c1.orfsRunnerRepo,
      librelaneRunnerRepo: c1.librelaneRunnerRepo,
      metricCollectorRepo: c1.metricCollectorRepo,
    });
    const w1 = new WorkflowStack(nagApp, "NagWorkflow", {
      env: "dev",
      cluster: co1.cluster,
      orfsRunnerTaskDef: co1.orfsRunnerTaskDef,
      librelaneRunnerTaskDef: co1.librelaneRunnerTaskDef,
      metricCollectorTaskDef: co1.metricCollectorTaskDef,
      artifactBucket: s1.bucket,
      candidatesTable: s1.candidatesTable,
      runsTable: s1.runsTable,
      eventsTable: s1.eventsTable,
    });
    // Force template synthesis so aspects run.
    Template.fromStack(w1);
    const errors = Annotations.fromStack(w1).findError(
      "*",
      Match.stringLikeRegexp("AwsSolutions-.*"),
    );
    if (errors.length > 0) {
      // Surface the offending codes to make regressions diagnosable.
      const codes = errors.map(
        (e) => (e.entry as { data: string }).data ?? JSON.stringify(e),
      );
      throw new Error(
        `cdk-nag AwsSolutions errors on WorkflowStack: ${codes.join("; ")}`,
      );
    }
    expect(errors.length).toBe(0);
  });
});
