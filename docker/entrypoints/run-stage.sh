#!/usr/bin/env bash
# docker/entrypoints/run-stage.sh
#
# Uniform ENTRYPOINT used by all three L1 images (orfs-runner, librelane-runner,
# metric-collector). The SFN Map state sets the env-var contract:
#
#   RUN_ID                   — ULID from Spec
#   STAGE                    — one of rtl-build|synth|pnr|signoff|metrics|sim
#   INPUT_S3_URI             — s3://... or file://... (tests use file://)
#   OUTPUT_S3_URI            — s3://... or file://...
#   SIMULATE_SPOT_RECLAIM    — "1" → sleep then exit 143 (KG-D contract)
#   STAGE_COMMAND            — the actual tool invocation for this stage
#
# Per spec §4.3, stage outputs land at runs/{RUN_ID}/staging/{STAGE}/ so that
# the Finalize Lambda can later CopyObject them into runs/{RUN_ID}/final/.
#
# Exit codes:
#   0   — stage succeeded
#   2   — missing required env var (operator error; SFN ValidateSpec catches)
#   143 — simulated Spot reclaim (matches SIGTERM default in bash: 128+15)
#   *   — tool's own exit code, propagated unchanged
set -euo pipefail

die() { echo "run-stage.sh: $*" >&2; exit 2; }

# NB: `: "${VAR:?}" || die` looks like it would dispatch to die on missing
# vars, but bash exits the shell when `:?` fires (even inside `||`), so die
# never runs. Use explicit `[[ -n ... ]]` checks so `die` can emit the
# operator-friendly message + the stable exit-2 code the SFN ValidateSpec
# test suite asserts on.
[[ -n "${RUN_ID:-}" ]]        || die "RUN_ID required"
[[ -n "${STAGE:-}" ]]         || die "STAGE required"
[[ -n "${INPUT_S3_URI:-}" ]]  || die "INPUT_S3_URI required"
[[ -n "${OUTPUT_S3_URI:-}" ]] || die "OUTPUT_S3_URI required"
[[ -n "${STAGE_COMMAND:-}" ]] || die "STAGE_COMMAND required"

SIMULATE_SPOT_RECLAIM="${SIMULATE_SPOT_RECLAIM:-0}"
SIMULATE_SPOT_RECLAIM_DELAY_S="${SIMULATE_SPOT_RECLAIM_DELAY_S:-3}"

# KG-D (spec §10): deterministic Spot reclaim injection. 143 = 128 + SIGTERM(15),
# matching what Fargate Spot sends on reclaim. SFN retry policy treats this as
# SpotReclaimed and retries up to MaxAttempts=2.
if [[ "$SIMULATE_SPOT_RECLAIM" == "1" ]]; then
  echo "SIMULATE_SPOT_RECLAIM=1: sleeping ${SIMULATE_SPOT_RECLAIM_DELAY_S}s then exiting 143" >&2
  sleep "$SIMULATE_SPOT_RECLAIM_DELAY_S"
  exit 143
fi

# Resolve OUTPUT staging directory. For file:// URIs used in tests, write
# directly; for s3:// URIs in production, write locally then `aws s3 sync`
# on exit.
case "$OUTPUT_S3_URI" in
  file://*)
    OUTPUT_LOCAL="${OUTPUT_S3_URI#file://}"
    USE_S3=0
    ;;
  s3://*)
    OUTPUT_LOCAL="$(mktemp -d)"
    USE_S3=1
    ;;
  *)
    die "OUTPUT_S3_URI must start with s3:// or file://"
    ;;
esac

export STAGE_WORK_DIR="${OUTPUT_LOCAL}/runs/${RUN_ID}/staging/${STAGE}"
mkdir -p "$STAGE_WORK_DIR"

case "$INPUT_S3_URI" in
  file://*)
    INPUT_LOCAL="${INPUT_S3_URI#file://}"
    ;;
  s3://*)
    INPUT_LOCAL="$(mktemp -d)"
    aws s3 sync "$INPUT_S3_URI" "$INPUT_LOCAL"
    ;;
  *)
    die "INPUT_S3_URI must start with s3:// or file://"
    ;;
esac
export STAGE_INPUT_DIR="$INPUT_LOCAL"

echo "run-stage: RUN_ID=$RUN_ID STAGE=$STAGE INPUT=$STAGE_INPUT_DIR OUTPUT=$STAGE_WORK_DIR" >&2
rc=0
bash -c "$STAGE_COMMAND" || rc=$?

if [[ "$USE_S3" == "1" && "$rc" == "0" ]]; then
  aws s3 sync "$OUTPUT_LOCAL" "$OUTPUT_S3_URI"
fi

exit "$rc"
