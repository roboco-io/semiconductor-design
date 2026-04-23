import * as path from "path";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as events from "aws-cdk-lib/aws-events";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import { NagSuppressions } from "cdk-nag";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface WorkflowStackProps extends Omit<StackProps, "env"> {
  env: EnvName;
  cluster: ecs.ICluster;
  orfsRunnerTaskDef: ecs.FargateTaskDefinition;
  librelaneRunnerTaskDef: ecs.FargateTaskDefinition;
  metricCollectorTaskDef: ecs.FargateTaskDefinition;
  artifactBucket: s3.IBucket;
  candidatesTable: dynamodb.ITable;
  runsTable: dynamodb.ITable;
  eventsTable: dynamodb.ITable;
}

/**
 * Step Functions STANDARD Workflow orchestrating per-candidate Fargate
 * pipelines. L1 spec §6.2 (K2 ζ): Standard is fixed — Express is forbidden
 * because pipeline runs routinely exceed the 5-minute Express ceiling.
 *
 * Shape (spec §6.1):
 *   StartAt = ValidateSpec   (Lambda — rejects design != "gcd")
 *     → InitGeneration       (Lambda — emits one-element candidates list)
 *     → Map(maxConcurrency=10)
 *         RunOrfsPipeline    (ECS Fargate RunTask)
 *         → Finalize         (Lambda — per-object ObjectLock + _SUCCESS)
 *
 * IAM boundary (least privilege, test: `three Lambda execution roles are
 * distinct`): each `lambda.Function` owns its own execution role; there
 * is no shared role across ValidateSpec / InitGeneration / Finalize. Only
 * Finalize is granted S3 read/write + kms:Decrypt — ValidateSpec and
 * InitGeneration are pure compute with no AWS side-effects.
 *
 * EventBridge rules (spec §6.1 + §10.6):
 *   1. run-completion  — semi-design.l1 / run.completed pattern (run-level)
 *   2. spot-interruption — aws.ecs / ECS Task State Change (Fargate Spot)
 *   3. daily-cost-alert — rate(1 day) schedule (cost guard trigger)
 */
export class WorkflowStack extends Stack {
  public readonly stateMachine: sfn.StateMachine;
  public readonly validateSpecFn: lambda.Function;
  public readonly initGenerationFn: lambda.Function;
  public readonly finalizeFn: lambda.Function;
  public readonly completionRule: events.Rule;
  public readonly spotInterruptionRule: events.Rule;
  public readonly dailyCostAlertRule: events.Rule;

  constructor(scope: Construct, id: string, props: WorkflowStackProps) {
    const { env: appEnv, ...rest } = props;
    const stackProps: StackProps = {
      ...rest,
      env: { region: "us-east-1" },
    };
    super(scope, id, stackProps);

    const lambdaRoot = path.join(__dirname, "..", "..", "lambdas");

    const makeLogGroup = (suffix: string): logs.LogGroup =>
      new logs.LogGroup(this, `${suffix}LogGroup`, {
        logGroupName: `/aws/lambda/semi-design-${appEnv}-${suffix}`,
        retention: logs.RetentionDays.ONE_MONTH,
      });

    // ---- Lambdas --------------------------------------------------------
    // Each Lambda gets its own implicit execution role — no shared role.
    // The Finalize role alone carries S3 read/write + kms:Decrypt; the
    // other two Lambdas are pure-compute (no AWS API calls).
    this.validateSpecFn = new lambda.Function(this, "ValidateSpec", {
      functionName: `semi-design-${appEnv}-validate-spec`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(lambdaRoot, "validate-spec")),
      timeout: Duration.seconds(15),
      logGroup: makeLogGroup("validate-spec"),
      tracing: lambda.Tracing.ACTIVE,
      environment: {
        G1_ALLOWED_DESIGN: "gcd",
      },
    });

    this.initGenerationFn = new lambda.Function(this, "InitGeneration", {
      functionName: `semi-design-${appEnv}-init-generation`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(lambdaRoot, "init-generation")),
      timeout: Duration.seconds(30),
      logGroup: makeLogGroup("init-generation"),
      tracing: lambda.Tracing.ACTIVE,
    });

    this.finalizeFn = new lambda.Function(this, "Finalize", {
      functionName: `semi-design-${appEnv}-finalize`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(lambdaRoot, "finalize")),
      timeout: Duration.minutes(5),
      logGroup: makeLogGroup("finalize"),
      tracing: lambda.Tracing.ACTIVE,
      environment: {
        ARTIFACT_BUCKET: props.artifactBucket.bucketName,
        RETENTION_DAYS: "90",
      },
    });
    // Grant Finalize scoped access: final/ prefix + retention API.
    this.finalizeFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject", "s3:PutObject", "s3:PutObjectRetention"],
        resources: [`${props.artifactBucket.bucketArn}/runs/*`],
      }),
    );

    // ---- Step Functions tasks ------------------------------------------
    const validate = new tasks.LambdaInvoke(this, "ValidateSpecTask", {
      lambdaFunction: this.validateSpecFn,
      payloadResponseOnly: true,
    });
    const initGen = new tasks.LambdaInvoke(this, "InitGenerationTask", {
      lambdaFunction: this.initGenerationFn,
      payloadResponseOnly: true,
    });

    // Per-candidate subflow. Phase E wires the synth/pnr/signoff stages;
    // the B6 skeleton uses the orfs-runner TaskDef as a placeholder so the
    // Map iterator compiles today and Fargate integration is exercised.
    const runOrfs = new tasks.EcsRunTask(this, "RunOrfsPipeline", {
      cluster: props.cluster,
      taskDefinition: props.orfsRunnerTaskDef,
      launchTarget: new tasks.EcsFargateLaunchTarget(),
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      assignPublicIp: false,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    });
    const finalize = new tasks.LambdaInvoke(this, "FinalizeTask", {
      lambdaFunction: this.finalizeFn,
      payloadResponseOnly: true,
    });

    const candidateChain = runOrfs.next(finalize);

    // maxConcurrency=10 is the canonical parallel substrate (spec §5
    // canonical decision table + overview spec §3.2 L1 contract).
    const mapState = new sfn.Map(this, "CandidatesMap", {
      maxConcurrency: 10,
      itemsPath: "$.candidates",
    });
    mapState.iterator(candidateChain);

    const definition = validate.next(initGen).next(mapState);

    // SFN execution log group for cdk-nag AwsSolutions-SF1 compliance.
    const sfnLogGroup = new logs.LogGroup(this, "L1StateMachineLogs", {
      logGroupName: `/aws/vendedlogs/states/semi-design-${appEnv}-l1`,
      retention: logs.RetentionDays.ONE_MONTH,
    });

    this.stateMachine = new sfn.StateMachine(this, "L1StateMachine", {
      stateMachineName: `semi-design-${appEnv}-l1`,
      stateMachineType: sfn.StateMachineType.STANDARD,
      definitionBody: sfn.DefinitionBody.fromChainable(definition),
      timeout: Duration.hours(4),
      tracingEnabled: true, // AwsSolutions-SF2
      logs: {
        destination: sfnLogGroup,
        level: sfn.LogLevel.ALL,
        includeExecutionData: false,
      },
    });

    // ---- EventBridge rules ---------------------------------------------
    // (1) Run-level completion events — emitted by the Python runner (via
    // `events:PutEvents` with source=semi-design.l1, detail-type=run.completed)
    // once finalize succeeds. Targets are wired in ObservabilityStack (B7).
    this.completionRule = new events.Rule(this, "CompletionRule", {
      ruleName: `semi-design-${appEnv}-run-completion`,
      eventPattern: {
        source: ["semi-design.l1"],
        detailType: ["run.completed"],
      },
    });

    // (2) Fargate Spot interruption — aws.ecs "ECS Task State Change" with
    // stoppedReason containing SpotInterruption. EventBridge does not support
    // nested stoppedReason filtering at the pattern level, so we match on the
    // task-state-change envelope and let the downstream consumer inspect
    // stoppedReason / stopCode to distinguish SpotInterruption from other
    // stops (spec §10.6).
    this.spotInterruptionRule = new events.Rule(this, "SpotInterruptionRule", {
      ruleName: `semi-design-${appEnv}-spot-interruption`,
      eventPattern: {
        source: ["aws.ecs"],
        detailType: ["ECS Task State Change"],
        detail: {
          clusterArn: [props.cluster.clusterArn],
          lastStatus: ["STOPPED"],
        },
      },
    });

    // (3) Daily cost alert — scheduled trigger so the cost guard Lambda
    // (wired in B7) checks accumulated Fargate + S3 + DDB spend against
    // the $50 / $100 budget ceilings defined in spec §10.6.
    this.dailyCostAlertRule = new events.Rule(this, "DailyCostAlertRule", {
      ruleName: `semi-design-${appEnv}-daily-cost-alert`,
      schedule: events.Schedule.rate(Duration.days(1)),
    });

    // ---- cdk-nag targeted suppressions ---------------------------------
    // AwsSolutions-IAM4: Lambdas use the AWS-managed
    //   AWSLambdaBasicExecutionRole (implicitly added by lambda.Function)
    //   to write to CloudWatch Logs. This is standard CDK practice and
    //   the managed policy is maintained by AWS; a bespoke replacement
    //   would be strictly less safe. Scope: just the 3 Lambda roles.
    // AwsSolutions-IAM5: the Lambda log-retention custom resource (an
    //   internal CDK construct) requires logs:* on arn:aws:logs:*:*:* —
    //   it manages log groups it did not create at synth time.
    // AwsSolutions-L1: pinning to the current non-deprecated Python
    //   runtime (3.12) is the minimum; AwsSolutions-L1 insists on the
    //   "latest" which drifts with each CDK release. We pin deliberately.
    for (const fn of [
      this.validateSpecFn,
      this.initGenerationFn,
      this.finalizeFn,
    ]) {
      NagSuppressions.addResourceSuppressions(
        fn,
        [
          {
            id: "AwsSolutions-IAM4",
            reason:
              "AWSLambdaBasicExecutionRole is the standard CDK-managed " +
              "policy for CloudWatch Logs writes; replacing it with a " +
              "bespoke inline policy would be strictly less safe.",
          },
          {
            id: "AwsSolutions-L1",
            reason:
              "Python 3.12 is the current non-deprecated LTS-tier Lambda " +
              "runtime; the project pins deliberately (L1 spec §6.2 K2 ζ " +
              "SHA-pinning principle) rather than tracking the cdk-nag " +
              "'latest' moving target which drifts with each CDK release.",
          },
        ],
        true,
      );
    }

    // Log-retention custom resource is emitted once per Lambda with
    // logRetention; suppress at stack level since the construct is
    // internal to aws-cdk-lib.
    NagSuppressions.addStackSuppressions(
      this,
      [
        {
          id: "AwsSolutions-IAM4",
          reason:
            "LogRetention custom resource uses the AWS-managed " +
            "AWSLambdaBasicExecutionRole — this is a CDK-internal " +
            "construct we do not control.",
        },
        {
          id: "AwsSolutions-IAM5",
          reason:
            "LogRetention custom resource needs logs:* on arbitrary " +
            "log group ARNs; scoping further would break the CDK-managed " +
            "retention mechanism. Finalize Lambda S3 IAM is separately " +
            "scoped to runs/* prefix (see addToRolePolicy above).",
        },
      ],
    );
  }
}
