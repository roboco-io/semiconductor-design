import { Stack, StackProps } from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as kms from "aws-cdk-lib/aws-kms";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface ComputeStackProps extends Omit<StackProps, "env"> {
  env: EnvName;
  vpc: ec2.IVpc;
  bucketCmk: kms.IKey;
  artifactBucketArn: string;
  orfsRunnerRepo: ecr.IRepository;
  librelaneRunnerRepo: ecr.IRepository;
  metricCollectorRepo: ecr.IRepository;
}

/**
 * ECS Fargate-only cluster + 3 runtime TaskDefs + kg-c2-smoke TaskDef.
 * Spec §6.1 / §6.3 / Codex 3rd-round new #5:
 *   - ephemeralStorageGiB: 21 on every TaskDef (K2 ζ: Fargate 한도 200 GiB)
 *   - kms:Decrypt scoped to bucketCmk only (minimum-principle). S3 객체
 *     해독만이 런타임 필요. Bare "*" forbidden: the test
 *     `task role kms:Decrypt is scoped to specific CMK ARNs, never '*'`
 *     is the regression guard.
 *   - secretsmanager:GetSecretValue ONLY on kg-c2-smoke task role (KG-C2
 *     smoke probe reads a seed secret). Secret에 연결된 AWS-managed CMK
 *     decrypt는 Secrets Manager의 key policy가 implicit grant하므로 task
 *     role에 별도 kms:Decrypt 부여 불필요.
 */
export class ComputeStack extends Stack {
  public readonly cluster: ecs.Cluster;
  public readonly orfsRunnerTaskDef: ecs.FargateTaskDefinition;
  public readonly librelaneRunnerTaskDef: ecs.FargateTaskDefinition;
  public readonly metricCollectorTaskDef: ecs.FargateTaskDefinition;
  public readonly kgC2SmokeTaskDef: ecs.FargateTaskDefinition;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    const { env: appEnv, vpc, bucketCmk, artifactBucketArn, ...rest } = props;
    const stackProps: StackProps = {
      ...rest,
      env: { region: "us-east-1" },
    };
    super(scope, id, stackProps);

    this.cluster = new ecs.Cluster(this, "Cluster", {
      vpc,
      containerInsights: true,
      enableFargateCapacityProviders: true,
    });

    const makeRuntimeTaskRole = (roleId: string): iam.Role => {
      const role = new iam.Role(this, roleId, {
        assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      });
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["s3:GetObject", "s3:PutObject"],
          resources: [`${artifactBucketArn}/runs/*`],
        }),
      );
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: [
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:GetItem",
          ],
          resources: [
            `arn:aws:dynamodb:${this.region}:${this.account}:table/semi-design-${appEnv}-Candidates`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/semi-design-${appEnv}-Events`,
          ],
        }),
      );
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["logs:CreateLogStream", "logs:PutLogEvents"],
          resources: [
            `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/ecs/semi-design-${appEnv}*`,
          ],
        }),
      );
      role.addToPolicy(
        new iam.PolicyStatement({
          actions: ["kms:Decrypt"],
          resources: [bucketCmk.keyArn],
        }),
      );
      return role;
    };

    const makeFargateTaskDef = (
      defId: string,
      family: string,
      repo: ecr.IRepository,
      extraRole?: (role: iam.Role) => void,
    ): ecs.FargateTaskDefinition => {
      const taskRole = makeRuntimeTaskRole(`${defId}TaskRole`);
      if (extraRole) {
        extraRole(taskRole);
      }
      const td = new ecs.FargateTaskDefinition(this, defId, {
        family: `semi-design-${appEnv}-${family}`,
        cpu: 4096,
        memoryLimitMiB: 16384,
        ephemeralStorageGiB: 21,
        taskRole,
      });
      td.addContainer("main", {
        image: ecs.ContainerImage.fromEcrRepository(repo),
        logging: ecs.LogDrivers.awsLogs({ streamPrefix: family }),
      });
      return td;
    };

    this.orfsRunnerTaskDef = makeFargateTaskDef(
      "OrfsRunner",
      "orfs-runner",
      props.orfsRunnerRepo,
    );
    this.librelaneRunnerTaskDef = makeFargateTaskDef(
      "LibrelaneRunner",
      "librelane-runner",
      props.librelaneRunnerRepo,
    );
    this.metricCollectorTaskDef = makeFargateTaskDef(
      "MetricCollector",
      "metric-collector",
      props.metricCollectorRepo,
    );

    this.kgC2SmokeTaskDef = makeFargateTaskDef(
      "KgC2Smoke",
      "kg-c2-smoke",
      props.metricCollectorRepo,
      (role) => {
        role.addToPolicy(
          new iam.PolicyStatement({
            actions: ["secretsmanager:GetSecretValue"],
            resources: [
              `arn:aws:secretsmanager:${this.region}:${this.account}:secret:/semi-design/*`,
            ],
          }),
        );
      },
    );
  }
}
