import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { EdaFlowStack } from "../lib/eda-flow-stack";

function synth() {
  const app = new App();
  const stack = new EdaFlowStack(app, "semi-design-eda-dev", { env: { account: "111111111111", region: "us-east-1" } });
  return Template.fromStack(stack);
}

test("provisions an S3 artifact bucket", () => {
  synth().resourceCountIs("AWS::S3::Bucket", 1);
});

test("provisions an ECR repository", () => {
  synth().resourceCountIs("AWS::ECR::Repository", 1);
});

test("provisions a Fargate task definition with awslogs + a log group", () => {
  const t = synth();
  t.resourceCountIs("AWS::ECS::TaskDefinition", 1);
  t.resourceCountIs("AWS::Logs::LogGroup", 1);
  t.hasResourceProperties("AWS::ECS::TaskDefinition", {
    RequiresCompatibilities: ["FARGATE"],
    Cpu: "4096",
    Memory: "16384",
  });
});

test("task role can write to the artifact bucket", () => {
  // S3 put permission present on some IAM policy
  synth().hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({ Action: Match.arrayWith(["s3:PutObject"]) }),
      ]),
    },
  });
});
