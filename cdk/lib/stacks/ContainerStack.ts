import { RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import * as ecr from "aws-cdk-lib/aws-ecr";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

/**
 * Application environment is disjoint from CDK's AWS `env`. The AWS
 * Environment is pinned in the constructor (see NetworkStack / StorageStack
 * for the same pattern) to keep synth deterministic.
 */
export interface ContainerStackProps extends Omit<StackProps, "env"> {
  env: EnvName;
}

/**
 * ECR container registry for the Fargate pipeline (spec §6.1).
 *
 * Provides 3 repositories consumed by the ComputeStack (B5) and built by
 * `docker/build-*.sh`:
 *   - orfs-runner        : OpenROAD flow runner image
 *   - librelane-runner   : LibreLane 2.4 flow runner image
 *   - metric-collector   : post-run metric aggregator image
 *
 * All repos enforce IMMUTABLE tags (reproducibility — no silent overwrite)
 * and scan-on-push (supply-chain hygiene). Repo names follow the contract
 * with docker/build-*.sh: `semi-design-${env}-${role}`.
 */
export class ContainerStack extends Stack {
  public readonly orfsRunnerRepo: ecr.Repository;
  public readonly librelaneRunnerRepo: ecr.Repository;
  public readonly metricCollectorRepo: ecr.Repository;

  constructor(scope: Construct, id: string, props: ContainerStackProps) {
    const { env: appEnv, ...rest } = props;
    const stackProps: StackProps = {
      ...rest,
      env: { region: "us-east-1" },
    };
    super(scope, id, stackProps);

    const removalPolicy =
      appEnv === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY;

    const repoDefaults = {
      imageTagMutability: ecr.TagMutability.IMMUTABLE,
      imageScanOnPush: true,
      removalPolicy,
    };

    this.orfsRunnerRepo = new ecr.Repository(this, "OrfsRunner", {
      repositoryName: `semi-design-${appEnv}-orfs-runner`,
      ...repoDefaults,
    });
    this.librelaneRunnerRepo = new ecr.Repository(this, "LibrelaneRunner", {
      repositoryName: `semi-design-${appEnv}-librelane-runner`,
      ...repoDefaults,
    });
    this.metricCollectorRepo = new ecr.Repository(this, "MetricCollector", {
      repositoryName: `semi-design-${appEnv}-metric-collector`,
      ...repoDefaults,
    });
  }
}
