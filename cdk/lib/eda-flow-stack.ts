import { Stack, StackProps, RemovalPolicy, Duration } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as logs from "aws-cdk-lib/aws-logs";

/**
 * 최소 one-shot Fargate EDA flow 스택.
 * ORFS gcd를 native x86로 완주 → 두-시점 report_checks → S3.
 * Step Functions/DynamoDB/batch는 YAGNI (후속). on-demand only.
 */
export class EdaFlowStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const artifacts = new s3.Bucket(this, "Artifacts", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const repo = new ecr.Repository(this, "RunnerRepo", {
      imageScanOnPush: true,
      removalPolicy: RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    const logGroup = new logs.LogGroup(this, "RunnerLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    // default VPC 사용 (NAT 없는 public subnet + assignPublicIp).
    const vpc = ec2.Vpc.fromLookup(this, "DefaultVpc", { isDefault: true });
    const cluster = new ecs.Cluster(this, "Cluster", { vpc });

    const taskDef = new ecs.FargateTaskDefinition(this, "RunnerTask", {
      cpu: 4096,
      memoryLimitMiB: 16384,
      ephemeralStorageGiB: 50,
      runtimePlatform: {
        cpuArchitecture: ecs.CpuArchitecture.X86_64,
        operatingSystemFamily: ecs.OperatingSystemFamily.LINUX,
      },
    });

    artifacts.grantWrite(taskDef.taskRole);

    taskDef.addContainer("runner", {
      image: ecs.ContainerImage.fromEcrRepository(repo, "latest"),
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: "eda-flow", logGroup }),
      environment: { ARTIFACT_BUCKET: artifacts.bucketName, DESIGN: "gcd" },
    });
  }
}
