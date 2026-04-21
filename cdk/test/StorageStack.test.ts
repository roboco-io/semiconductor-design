import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { StorageStack } from "../lib/stacks/StorageStack";

describe("StorageStack", () => {
  const app = new App({ context: { env: "dev" } });
  const stack = new StorageStack(app, "StorageStackTest", { env: "dev" });
  const template = Template.fromStack(stack);

  it("creates an S3 bucket with ObjectLockEnabled=true at creation (Codex 3rd-round)", () => {
    template.hasResourceProperties("AWS::S3::Bucket", {
      ObjectLockEnabled: true,
      VersioningConfiguration: { Status: "Enabled" },
      ObjectLockConfiguration: Match.objectLike({
        ObjectLockEnabled: "Enabled",
        Rule: { DefaultRetention: { Mode: "GOVERNANCE", Days: 90 } },
      }),
    });
  });

  it("bucket has lifecycle transitioning to GLACIER_IR at 90 days", () => {
    template.hasResourceProperties("AWS::S3::Bucket", {
      LifecycleConfiguration: Match.objectLike({
        Rules: Match.arrayWith([
          Match.objectLike({
            Status: "Enabled",
            Transitions: Match.arrayWith([
              Match.objectLike({ StorageClass: "GLACIER_IR", TransitionInDays: 90 }),
            ]),
          }),
        ]),
      }),
    });
  });

  it("creates exactly 4 DynamoDB tables with Events TTL enabled", () => {
    template.resourceCountIs("AWS::DynamoDB::Table", 4);
    template.hasResourceProperties("AWS::DynamoDB::Table", {
      TableName: Match.stringLikeRegexp("Events"),
      TimeToLiveSpecification: { AttributeName: "ttl", Enabled: true },
    });
  });

  it("creates a KMS CMK with key rotation enabled", () => {
    template.resourceCountIs("AWS::KMS::Key", 1);
    template.hasResourceProperties("AWS::KMS::Key", { EnableKeyRotation: true });
  });

  it("exposes bucketCmk as a public readonly property", () => {
    expect(stack.bucketCmk).toBeDefined();
    expect(stack.bucketCmk.keyArn).toBeDefined();
  });
});
