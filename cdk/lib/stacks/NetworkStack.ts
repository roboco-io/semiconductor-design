import { Stack, StackProps } from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface NetworkStackProps extends Omit<StackProps, "env"> {
  env: EnvName;
}

/**
 * VPC + 2 AZ private subnets. No NAT gateway — all egress goes through
 * VPC endpoints (spec §6.1). The 9 endpoints cover every AWS service the
 * Fargate tasks + Lambda reach at runtime: S3 (Gateway), ECR api/dkr,
 * CloudWatch Logs, Secrets Manager, SSM, STS, CloudWatch Monitoring, KMS.
 */
export class NetworkStack extends Stack {
  public readonly vpc: ec2.Vpc;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    const { env: _envName, ...rest } = props;
    // VPC endpoint ServiceName resolution requires a concrete region; without
    // it CDK emits Fn::Join tokens. Default to us-east-1 so synth produces
    // literal service names. Per-env account/region pinning lives in bin/.
    const stackProps: StackProps = {
      ...rest,
      env: { region: "us-east-1" },
    };
    super(scope, id, stackProps);

    this.vpc = new ec2.Vpc(this, "Vpc", {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: "private-isolated",
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    });

    // Using GatewayVpcEndpointAwsService.S3 directly produces a tokenised
    // ServiceName (Fn::Join with AWS::Region). Since this stack pins region
    // above, we build a literal service name so CloudFormation sees a plain
    // string — matches how the other 8 interface endpoints resolve.
    const region = stackProps.env!.region!;
    this.vpc.addGatewayEndpoint("S3Gateway", {
      service: { name: `com.amazonaws.${region}.s3` },
    });

    const interfaceServices: Array<{ id: string; svc: ec2.InterfaceVpcEndpointAwsService }> = [
      { id: "EcrApi", svc: ec2.InterfaceVpcEndpointAwsService.ECR },
      { id: "EcrDkr", svc: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER },
      { id: "Logs", svc: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS },
      { id: "SecretsManager", svc: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER },
      { id: "Ssm", svc: ec2.InterfaceVpcEndpointAwsService.SSM },
      { id: "Sts", svc: ec2.InterfaceVpcEndpointAwsService.STS },
      { id: "Monitoring", svc: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_MONITORING },
      { id: "Kms", svc: ec2.InterfaceVpcEndpointAwsService.KMS },
    ];

    for (const { id: endpointId, svc } of interfaceServices) {
      this.vpc.addInterfaceEndpoint(endpointId, {
        service: svc,
        subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
        privateDnsEnabled: true,
      });
    }
  }
}
