"""semi-run CLI entry point. Subcommands operate on Spec/RunArtifact lifecycle.

`init` validates spec + puts to S3 + records Runs row.
`lockfile-verify` emits the JSON output for G1 exit criterion 6.
`auth login` wraps `aws sso login` so operator onboarding is one command.
`submit` starts the SFN execution for a prepared run.
`status` joins DDB Candidates status with SFN DescribeExecution.
`artifacts` mirrors `s3://bucket/runs/<run_id>/final/` to a local dest dir.
`cost` reads the accumulated `Runs.total_cost_usd` for a run.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import click
import yaml

from semi_design_runner import __version__
from semi_design_runner.aws.clients import make_client
from semi_design_runner.aws.ddb import put_candidate_with_count
from semi_design_runner.aws.s3 import download_final, put_spec
from semi_design_runner.aws.sfn import describe_execution, start_execution
from semi_design_runner.lockfile import load_lockfile, verify_scope
from semi_design_runner.schemas import Spec
from semi_design_runner.validator import RejectedNotInG1Scope, validate_spec_for_g1


@click.group()
@click.version_option(__version__, prog_name="semi-run")
def main() -> None:
    """L1 Process runner CLI."""


@main.command("init")
@click.option("--spec", "spec_path", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--bucket", type=str, default="semi-design")
@click.option("--profile", type=str, default="semi-design-operator")
def init_cmd(spec_path: Path, bucket: str, profile: str) -> None:
    raw = yaml.safe_load(spec_path.read_text())
    spec = Spec.model_validate(raw)
    try:
        validate_spec_for_g1(spec)
    except RejectedNotInG1Scope as exc:
        click.echo(f"RejectedNotInG1Scope: {exc}", err=True)
        raise SystemExit(2)

    s3 = make_client("s3", profile=profile)
    ddb = make_client("dynamodb", profile=profile)
    uri = put_spec(s3, bucket=bucket, run_id=spec.run_id, spec_yaml=spec_path.read_text())
    put_candidate_with_count(
        ddb,
        table="Candidates",
        run_id=spec.run_id,
        gen=0,
        cand=0,
        attributes={"status": "in_progress"},
    )
    # cache last-run-id for Makefile convenience
    Path(".last-run-id").write_text(spec.run_id)
    click.echo(json.dumps({"run_id": spec.run_id, "spec_uri": uri}))


@main.command("lockfile-verify")
@click.option("--lockfile", "lockfile_path", type=click.Path(exists=True, path_type=Path),
              default=Path("lockfile.yaml"))
@click.option("--scope", type=click.Choice(["l1", "full"]), default="l1")
def lockfile_verify_cmd(lockfile_path: Path, scope: str) -> None:
    lockfile = load_lockfile(lockfile_path)
    result = verify_scope(lockfile, scope=scope)
    click.echo(json.dumps(result, indent=2))
    if not result["verified"]:
        raise SystemExit(1)


@main.group("auth")
def auth_group() -> None:
    """AWS authentication helpers."""


@auth_group.command("login")
@click.option("--profile", type=str, default="semi-design-operator")
def auth_login_cmd(profile: str) -> None:
    proc = subprocess.run(
        ["aws", "sso", "login", "--profile", profile],
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


@main.command("submit")
@click.option("--run-id", type=str, required=True)
@click.option("--state-machine-arn", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def submit_cmd(run_id: str, state_machine_arn: str, profile: str) -> None:
    sfn = make_client("stepfunctions", profile=profile)
    arn = start_execution(
        sfn,
        state_machine_arn=state_machine_arn,
        run_id=run_id,
        input_payload={"run_id": run_id},
    )
    click.echo(arn)


@main.command("status")
@click.option("--run-id", type=str, required=True)
@click.option("--execution-arn", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def status_cmd(run_id: str, execution_arn: str, profile: str) -> None:
    ddb = make_client("dynamodb", profile=profile)
    sfn = make_client("stepfunctions", profile=profile)
    ddb_resp = ddb.get_item(
        TableName="Candidates",
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": "gen#0#cand#0"},
        },
        ProjectionExpression="status",
    )
    ddb_status = ddb_resp.get("Item", {}).get("status", {}).get("S", "unknown")
    sfn_desc = describe_execution(sfn, execution_arn=execution_arn)
    click.echo(json.dumps({
        "run_id": run_id,
        "ddb_status": ddb_status,
        "sfn_status": sfn_desc.get("status", "unknown"),
    }))


@main.command("artifacts")
@click.option("--run-id", type=str, required=True)
@click.option("--bucket", type=str, required=True)
@click.option("--dest", type=click.Path(path_type=Path), required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def artifacts_cmd(run_id: str, bucket: str, dest: Path, profile: str) -> None:
    s3 = make_client("s3", profile=profile)
    dest.mkdir(parents=True, exist_ok=True)
    download_final(s3, bucket=bucket, run_id=run_id, dest=dest)
    click.echo(str(dest))


@main.command("cost")
@click.option("--run-id", type=str, required=True)
@click.option("--profile", type=str, default="semi-design-operator")
def cost_cmd(run_id: str, profile: str) -> None:
    ddb = make_client("dynamodb", profile=profile)
    resp = ddb.get_item(
        TableName="Runs",
        Key={"run_id": {"S": run_id}},
        ProjectionExpression="total_cost_usd",
    )
    raw = resp.get("Item", {}).get("total_cost_usd", {}).get("N", "0")
    click.echo(json.dumps({"run_id": run_id, "total_cost_usd": float(raw)}))
