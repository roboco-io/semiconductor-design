import { App } from "aws-cdk-lib";
import { Template, Match } from "aws-cdk-lib/assertions";
import { StorageStack } from "../lib/stacks/StorageStack";
import { ObservabilityStack } from "../lib/stacks/ObservabilityStack";

describe("ObservabilityStack", () => {
  const app = new App({ context: { env: "dev" } });
  // Only StorageStack is a real dependency (for DDB ARNs).
  const storage = new StorageStack(app, "StorageO", { env: "dev" });
  const stack = new ObservabilityStack(app, "ObservabilityO", {
    env: "dev",
    candidatesTable: storage.candidatesTable,
    runsTable: storage.runsTable,
  });
  const template = Template.fromStack(stack);

  it("creates exactly one CloudWatch dashboard", () => {
    template.resourceCountIs("AWS::CloudWatch::Dashboard", 1);
  });

  it("creates the spot-reclaim-rate alarm with threshold 0.3", () => {
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("spot-reclaim-rate"),
      Threshold: 0.3,
    });
  });

  it("creates the SFN failure alarm", () => {
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("sfn-failure"),
    });
  });

  it("creates the cost-per-candidate alarm with threshold 5", () => {
    template.hasResourceProperties("AWS::CloudWatch::Alarm", {
      AlarmName: Match.stringLikeRegexp("cost-per-candidate"),
      Threshold: 5,
    });
  });

  it("creates exactly two budget alarms ($50 and $100)", () => {
    template.resourceCountIs("AWS::Budgets::Budget", 2);
    template.hasResourceProperties("AWS::Budgets::Budget", {
      Budget: Match.objectLike({
        BudgetLimit: { Amount: 50, Unit: "USD" },
      }),
    });
    template.hasResourceProperties("AWS::Budgets::Budget", {
      Budget: Match.objectLike({
        BudgetLimit: { Amount: 100, Unit: "USD" },
      }),
    });
  });

  it("dashboard name follows semi-design-{env}-l1 convention", () => {
    template.hasResourceProperties("AWS::CloudWatch::Dashboard", {
      DashboardName: "semi-design-dev-l1",
    });
  });
});
