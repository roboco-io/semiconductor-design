export type EnvName = "dev" | "prod";

export interface AppContext {
  env: EnvName;
}

export function resolveContext(raw: { env?: string }): AppContext {
  const env = raw.env ?? "dev";
  if (env !== "dev" && env !== "prod") {
    throw new Error(`env must be 'dev' or 'prod', got '${env}'`);
  }
  return { env };
}
