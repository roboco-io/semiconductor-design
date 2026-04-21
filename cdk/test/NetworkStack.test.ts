import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { NetworkStack } from "../lib/stacks/NetworkStack";

describe("NetworkStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new NetworkStack(app, "NetworkStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates a VPC with 2 private subnets and no NAT gateway", () => {
    template.resourceCountIs("AWS::EC2::VPC", 1);
    template.resourceCountIs("AWS::EC2::NatGateway", 0);
    const privateSubnets = template.findResources("AWS::EC2::Subnet", {
      Properties: { MapPublicIpOnLaunch: false },
    });
    expect(Object.keys(privateSubnets).length).toBe(2);
  });

  it("creates exactly the 9 required VPC endpoints", () => {
    template.resourceCountIs("AWS::EC2::VPCEndpoint", 9);

    const expectedInterfaceSuffixes = [
      "ecr.api",
      "ecr.dkr",
      "logs",
      "secretsmanager",
      "ssm",
      "sts",
      "monitoring",
      "kms",
    ];
    for (const suffix of expectedInterfaceSuffixes) {
      template.hasResourceProperties("AWS::EC2::VPCEndpoint", {
        VpcEndpointType: "Interface",
        ServiceName: Match.stringLikeRegexp(`com\\.amazonaws\\.[a-z0-9-]+\\.${suffix.replace(".", "\\.")}$`),
      });
    }
    template.hasResourceProperties("AWS::EC2::VPCEndpoint", {
      VpcEndpointType: "Gateway",
      ServiceName: Match.stringLikeRegexp(`com\\.amazonaws\\.[a-z0-9-]+\\.s3$`),
    });
  });
});
