import { Duration, Stack, StackProps } from "aws-cdk-lib";
import * as budgets from "aws-cdk-lib/aws-budgets";
import * as cw from "aws-cdk-lib/aws-cloudwatch";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

/**
 * CloudWatch dashboards + alarms per spec §6.1 + §14:
 *   - Spot reclaim rate (CloudWatch metric from ECS)
 *   - SFN failure rate
 *   - per-candidate cost (custom metric emitted by Finalize Lambda)
 *   - Candidates.ddb_write_count P99 (app-level — emitted by runner)
 *   - Budget alarms at $50 and $100 (AWS Budgets, not CloudWatch).
 */
export interface ObservabilityStackProps extends Omit<StackProps, "env"> {
  env: EnvName;
  candidatesTable: dynamodb.ITable;
  runsTable: dynamodb.ITable;
  notificationEmail?: string;
}

export class ObservabilityStack extends Stack {
  public readonly dashboard: cw.Dashboard;

  constructor(scope: Construct, id: string, props: ObservabilityStackProps) {
    const { env: appEnv, candidatesTable: _ct, runsTable: _rt, notificationEmail, ...rest } = props;
    super(scope, id, {
      ...rest,
      env: { region: "us-east-1" },
    });

    // candidatesTable / runsTable are accepted as IDependable inputs so the
    // dashboard can later add per-table widgets without re-importing — kept
    // unused at construction time on purpose (consumed by Phase E widget
    // expansion).
    void _ct;
    void _rt;

    this.dashboard = new cw.Dashboard(this, "L1Dashboard", {
      dashboardName: `semi-design-${appEnv}-l1`,
    });

    // Spot reclaim rate metric (ECS custom metric, namespace = semi-design/l1).
    const spotReclaimMetric = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "SpotReclaimRate",
      statistic: "Average",
      period: Duration.minutes(5),
    });
    new cw.Alarm(this, "SpotReclaimAlarm", {
      alarmName: `semi-design-${appEnv}-spot-reclaim-rate`,
      metric: spotReclaimMetric,
      threshold: 0.3,
      evaluationPeriods: 2,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // SFN failure rate: ratio of execution failures to starts.
    const sfnFailures = new cw.Metric({
      namespace: "AWS/States",
      metricName: "ExecutionsFailed",
      statistic: "Sum",
      period: Duration.minutes(15),
    });
    new cw.Alarm(this, "SfnFailureAlarm", {
      alarmName: `semi-design-${appEnv}-sfn-failure`,
      metric: sfnFailures,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // Cost per candidate > $5.
    const costPerCand = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "CostPerCandidateUsd",
      statistic: "Maximum",
      period: Duration.minutes(15),
    });
    new cw.Alarm(this, "CostPerCandidateAlarm", {
      alarmName: `semi-design-${appEnv}-cost-per-candidate`,
      metric: costPerCand,
      threshold: 5,
      evaluationPeriods: 1,
      comparisonOperator: cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
    });

    // Candidates.ddb_write_count P99 widget — the alarm is intentionally
    // omitted (KG-E asserts this from app-level counter, not CloudWatch).
    const ddbWriteCount = new cw.Metric({
      namespace: "semi-design/l1",
      metricName: "CandidatesDdbWriteCount",
      statistic: "p99",
      period: Duration.minutes(60),
    });
    this.dashboard.addWidgets(
      new cw.GraphWidget({
        title: "Spot reclaim rate",
        left: [spotReclaimMetric],
      }),
      new cw.GraphWidget({
        title: "SFN failures",
        left: [sfnFailures],
      }),
      new cw.GraphWidget({
        title: "Cost / candidate (USD)",
        left: [costPerCand],
      }),
      new cw.GraphWidget({
        title: "Candidates.ddb_write_count P99",
        left: [ddbWriteCount],
      }),
    );

    // Budget alarms at $50 and $100. Cost filter tags require Tags.of(app)
    // to apply `project=semi-design-{env}` at the App level — wired in
    // bin/semi-design.ts.
    const makeBudget = (logicalId: string, amount: number): void => {
      new budgets.CfnBudget(this, logicalId, {
        budget: {
          budgetName: `semi-design-${appEnv}-${amount}usd`,
          budgetType: "COST",
          timeUnit: "MONTHLY",
          budgetLimit: { amount: amount, unit: "USD" },
          costFilters: {
            TagKeyValue: [`user:project$semi-design-${appEnv}`],
          },
        },
        notificationsWithSubscribers: notificationEmail
          ? [
              {
                notification: {
                  notificationType: "ACTUAL",
                  comparisonOperator: "GREATER_THAN",
                  threshold: 100,
                  thresholdType: "PERCENTAGE",
                },
                subscribers: [
                  {
                    subscriptionType: "EMAIL",
                    address: notificationEmail,
                  },
                ],
              },
            ]
          : [],
      });
    };
    makeBudget("Budget50", 50);
    makeBudget("Budget100", 100);
  }
}
