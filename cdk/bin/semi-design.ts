#!/usr/bin/env node
import "source-map-support/register";
import { App, Aspects, Tags } from "aws-cdk-lib";
import { AwsSolutionsChecks, NagSuppressions } from "cdk-nag";
import { EnvName, resolveContext } from "../lib/app-context";
import { NetworkStack } from "../lib/stacks/NetworkStack";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ContainerStack } from "../lib/stacks/ContainerStack";
import { ComputeStack } from "../lib/stacks/ComputeStack";
import { WorkflowStack } from "../lib/stacks/WorkflowStack";
import { ObservabilityStack } from "../lib/stacks/ObservabilityStack";

export interface BuildAppOptions {
  env: EnvName;
}

export function buildApp(opts: BuildAppOptions): App {
  const ctx = resolveContext({ env: opts.env });
  const app = new App({ context: { env: ctx.env } });
  // cdk-nag AwsSolutionsChecks attached to root App so every stack inherits.
  Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
  // Project tag is the cost-filter key for AWS Budgets in ObservabilityStack
  // (Budget.costFilters.TagKeyValue = ["user:project$semi-design-{env}"]).
  Tags.of(app).add("project", `semi-design-${ctx.env}`);

  const network = new NetworkStack(app, "NetworkStack", { env: ctx.env });
  NagSuppressions.addStackSuppressions(
    network,
    [
      {
        id: "AwsSolutions-VPC7",
        reason:
          "VPC Flow Log destination (CloudWatch Log Group + retention) is provisioned " +
          "by ObservabilityStack in Phase E. Adding it here would couple Network → " +
          "Observability before the log-group naming convention is finalized.",
      },
    ],
    true,
  );
  const storage = new StorageStack(app, "StorageStack", { env: ctx.env });
  NagSuppressions.addStackSuppressions(
    storage,
    [
      {
        id: "AwsSolutions-S1",
        reason:
          "S3 server access logs target bucket (with its own retention/lifecycle) is " +
          "provisioned by ObservabilityStack in Phase E. Dedicated logging-bucket " +
          "naming convention is not finalized — adding here would couple Storage → " +
          "Observability prematurely.",
      },
    ],
    true,
  );
  const container = new ContainerStack(app, "ContainerStack", { env: ctx.env });
  const compute = new ComputeStack(app, "ComputeStack", {
    env: ctx.env,
    vpc: network.vpc,
    bucketCmk: storage.bucketCmk,
    artifactBucketArn: storage.bucket.bucketArn,
    orfsRunnerRepo: container.orfsRunnerRepo,
    librelaneRunnerRepo: container.librelaneRunnerRepo,
    metricCollectorRepo: container.metricCollectorRepo,
  });
  const workflow = new WorkflowStack(app, "WorkflowStack", {
    env: ctx.env,
    cluster: compute.cluster,
    orfsRunnerTaskDef: compute.orfsRunnerTaskDef,
    librelaneRunnerTaskDef: compute.librelaneRunnerTaskDef,
    metricCollectorTaskDef: compute.metricCollectorTaskDef,
    artifactBucket: storage.bucket,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
    eventsTable: storage.eventsTable,
  });
  new ObservabilityStack(app, "ObservabilityStack", {
    env: ctx.env,
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
  });

  // Explicit cdk-nag suppressions with justification (spec §16.3 — every
  // suppression listed here, reviewed on PR).
  NagSuppressions.addStackSuppressions(
    compute,
    [
      {
        id: "AwsSolutions-IAM5",
        reason:
          "Fargate task role scopes s3:GetObject/PutObject to runs/* prefix. " +
          "kms:Decrypt is scoped to explicit CMK ARNs (bucketCmk + Secrets Manager CMK) — " +
          "verified by ComputeStack unit test and App-level cdk-nag test.",
      },
    ],
    true,
  );
  NagSuppressions.addStackSuppressions(
    workflow,
    [
      {
        id: "AwsSolutions-SF1",
        reason: "CloudWatch logging will be enabled in Phase E when real log groups exist.",
      },
    ],
    true,
  );

  return app;
}

if (require.main === module) {
  const rawEnv = process.env.CDK_CONTEXT_ENV ?? "dev";
  const ctx = resolveContext({ env: rawEnv });
  buildApp({ env: ctx.env });
}
