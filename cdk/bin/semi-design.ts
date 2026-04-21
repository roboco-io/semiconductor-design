#!/usr/bin/env node
import "source-map-support/register";
import { App, Aspects } from "aws-cdk-lib";
import { AwsSolutionsChecks } from "cdk-nag";
import { AppContext, EnvName, resolveContext } from "../lib/app-context";

export interface BuildAppOptions {
  env: EnvName;
}

export function buildApp(opts: BuildAppOptions): App {
  const ctx = resolveContext({ env: opts.env });
  const app = new App({
    context: { env: ctx.env },
  });
  // cdk-nag AwsSolutionsChecks attached to root App so every stack inherits.
  Aspects.of(app).add(new AwsSolutionsChecks({ verbose: true }));
  return app;
}

// Invoked by `cdk synth` / `cdk deploy`.
if (require.main === module) {
  const rawEnv = process.env.CDK_CONTEXT_ENV ?? "dev";
  const ctx = resolveContext({ env: rawEnv });
  buildApp({ env: ctx.env });
}
