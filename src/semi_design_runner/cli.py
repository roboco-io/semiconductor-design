"""semi-run CLI entry point. Subcommands operate on Spec/RunArtifact lifecycle.

`init` validates spec + puts to S3 + records Runs row.
`lockfile-verify` emits the JSON output for G1 exit criterion 6.
`auth login` wraps `aws sso login` so operator onboarding is one command.

Other subcommands (submit/status/artifacts/cost) ship in Task A15.
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
from semi_design_runner.aws.s3 import put_spec
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
    subprocess.run(
        ["aws", "sso", "login", "--profile", profile],
        check=False,
    )
