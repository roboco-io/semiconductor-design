import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { ContainerStack } from "../lib/stacks/ContainerStack";

describe("ContainerStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new ContainerStack(app, "ContainerStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates 3 ECR repositories", () => {
    template.resourceCountIs("AWS::ECR::Repository", 3);
  });

  it.each(["orfs-runner", "librelane-runner", "metric-collector"])(
    "creates ECR repo %s with immutable tags and scan-on-push",
    (name) => {
      template.hasResourceProperties("AWS::ECR::Repository", {
        RepositoryName: Match.stringLikeRegexp(name),
        ImageTagMutability: "IMMUTABLE",
        ImageScanningConfiguration: { ScanOnPush: true },
      });
    },
  );

  it("exposes all three repo ARNs as public properties", () => {
    expect(stack.orfsRunnerRepo.repositoryArn).toBeDefined();
    expect(stack.librelaneRunnerRepo.repositoryArn).toBeDefined();
    expect(stack.metricCollectorRepo.repositoryArn).toBeDefined();
  });
});
