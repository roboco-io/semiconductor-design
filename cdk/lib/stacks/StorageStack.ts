import { Duration, RemovalPolicy, Stack, StackProps } from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as kms from "aws-cdk-lib/aws-kms";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { EnvName } from "../app-context";

export interface StorageStackProps extends Omit<StackProps, "env"> {
  /**
   * Application environment — disjoint from CDK's AWS `env`. The AWS
   * Environment is pinned in the constructor (see NetworkStack for the
   * same pattern) to keep synth deterministic and avoid Fn::Join tokens.
   */
  env: EnvName;
}

/**
 * Artefact lake + metadata store for the research pipeline (spec §6.1, §6.2).
 *
 * Provides:
 *   - 1 KMS CMK with rotation (bucket + DDB encryption)
 *   - 1 S3 bucket with Object Lock enabled AT CREATION (GOVERNANCE 90d) +
 *     versioning + KMS encryption + SSL enforcement + Glacier-IR lifecycle
 *   - 4 DynamoDB tables: Runs, Generations, Candidates, Events (TTL on Events)
 *
 * Object Lock cannot be retrofitted to an existing bucket (S3 API), so it
 * MUST be declared on the initial L1 construct — hence `objectLockEnabled: true`
 * on the `s3.Bucket` props, not `addObjectLockConfiguration` later.
 */
export class StorageStack extends Stack {
  public readonly bucket: s3.Bucket;
  public readonly bucketCmk: kms.Key;
  public readonly runsTable: dynamodb.Table;
  public readonly generationsTable: dynamodb.Table;
  public readonly candidatesTable: dynamodb.Table;
  public readonly eventsTable: dynamodb.Table;

  constructor(scope: Construct, id: string, props: StorageStackProps) {
    const { env: appEnv, ...rest } = props;
    const stackProps: StackProps = {
      ...rest,
      env: { region: "us-east-1" },
    };
    super(scope, id, stackProps);

    const removalPolicy =
      appEnv === "prod" ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY;

    // ---- KMS CMK ---------------------------------------------------------
    this.bucketCmk = new kms.Key(this, "BucketCmk", {
      alias: `alias/semi-design-${appEnv}-bucket`,
      description: `Semi-design ${appEnv} CMK for S3 artefact lake + DDB tables`,
      enableKeyRotation: true,
      removalPolicy,
    });

    // ---- S3 artefact lake ------------------------------------------------
    this.bucket = new s3.Bucket(this, "ArtefactBucket", {
      bucketName: `semi-design-${this.account}-${this.region}`,
      // Object Lock MUST be enabled at creation — S3 forbids retroactive enable.
      objectLockEnabled: true,
      objectLockDefaultRetention: s3.ObjectLockRetention.governance(
        Duration.days(90),
      ),
      versioned: true,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: this.bucketCmk,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy,
      lifecycleRules: [
        {
          id: "transition-to-glacier-ir-90d",
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER_INSTANT_RETRIEVAL,
              transitionAfter: Duration.days(90),
            },
          ],
        },
      ],
    });

    // ---- DynamoDB tables -------------------------------------------------
    const commonTableProps: Omit<dynamodb.TableProps, "partitionKey"> = {
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.bucketCmk,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
      removalPolicy,
    };

    this.runsTable = new dynamodb.Table(this, "RunsTable", {
      ...commonTableProps,
      tableName: `semi-design-${appEnv}-Runs`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
    });

    this.generationsTable = new dynamodb.Table(this, "GenerationsTable", {
      ...commonTableProps,
      tableName: `semi-design-${appEnv}-Generations`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "gen", type: dynamodb.AttributeType.NUMBER },
    });

    this.candidatesTable = new dynamodb.Table(this, "CandidatesTable", {
      ...commonTableProps,
      tableName: `semi-design-${appEnv}-Candidates`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "gen_cand", type: dynamodb.AttributeType.STRING },
    });

    this.eventsTable = new dynamodb.Table(this, "EventsTable", {
      ...commonTableProps,
      tableName: `semi-design-${appEnv}-Events`,
      partitionKey: { name: "run_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "ts", type: dynamodb.AttributeType.STRING },
      // TTL attribute is declared here; the 90-day policy is enforced by the
      // Lambda writing items (it sets `ttl` = now + 90d). Spec §6.2.
      timeToLiveAttribute: "ttl",
    });
  }
}
