import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { buildApp } from "../bin/semi-design";

/**
 * Resource-type-count snapshot — stable across CDK version bumps because
 * we only hash the count of each resource type, not the full template.
 * Full-template snapshots would churn on every aws-cdk-lib upgrade.
 *
 * If this snapshot fails after a CDK upgrade, inspect whether the diff
 * adds/removes resource *types* (intentional) vs only adjusts properties
 * within types (false positive — update snapshot).
 */
function resourceTypeFingerprint(app: App): Record<string, Record<string, number>> {
  const fingerprint: Record<string, Record<string, number>> = {};
  const assembly = app.synth();
  for (const stack of assembly.stacks) {
    const counts: Record<string, number> = {};
    const resources = (stack.template.Resources ?? {}) as Record<string, { Type: string }>;
    for (const res of Object.values(resources)) {
      counts[res.Type] = (counts[res.Type] ?? 0) + 1;
    }
    fingerprint[stack.stackName] = counts;
  }
  return fingerprint;
}

describe("App resource-type fingerprint", () => {
  it("dev env fingerprint matches snapshot", () => {
    const app = buildApp({ env: "dev" });
    expect(resourceTypeFingerprint(app)).toMatchSnapshot();
  });
});

// Reference Template usage so the import is not flagged by ts-pruner.
void Template;
