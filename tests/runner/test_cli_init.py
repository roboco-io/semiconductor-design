from unittest.mock import patch

from click.testing import CliRunner

from semi_design_runner.cli import main

SPEC_YAML = """\
version: 1
run_id: 01HAAAA
design: gcd
stack: orfs
flow_parameters: {{}}
compute_budget_usd: 10.0
seed: 42
l1_lockfile_sha: "sha256:{sha}"
""".format(sha="a" * 64)


def test_cli_version_flag():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "semi-run" in result.output


def test_init_rejects_non_gcd_design(tmp_path):
    spec_file = tmp_path / "bad.yaml"
    spec_file.write_text(SPEC_YAML.replace("design: gcd", "design: ibex"))
    result = CliRunner().invoke(main, ["init", "--spec", str(spec_file)])
    assert result.exit_code != 0
    assert "RejectedNotInG1Scope" in result.output or "not in G1 scope" in result.output


def test_init_writes_spec_to_s3_on_success(tmp_path):
    spec_file = tmp_path / "gcd.yaml"
    spec_file.write_text(SPEC_YAML)
    with patch("semi_design_runner.cli.make_client") as mk_client, \
         patch("semi_design_runner.cli.put_spec", return_value="s3://b/x"), \
         patch("semi_design_runner.cli.put_candidate_with_count"):
        mk_client.return_value = object()  # any
        result = CliRunner().invoke(
            main,
            ["init", "--spec", str(spec_file), "--bucket", "b"],
        )
    assert result.exit_code == 0, result.output
    assert "s3://b/x" in result.output


def test_lockfile_verify_l1_scope(tmp_path):
    lock = tmp_path / "lockfile.yaml"
    lock.write_text(
        "version: 1\n"
        "commit_shas:\n"
        "  openroad: abc\n  librelane: def\n  yosys: ghi\n  open_pdks: jkl\n"
        "  verilator: null\n  cocotb: null\n  chipyard: null\n"
        "  gemmini: null\n  mlcommons_tiny: null\n"
        "container_digests:\n"
        "  orfs-runner: sha256:x\n  librelane-runner: sha256:y\n"
        "  metric-collector: sha256:z\n"
        "source_tarball_mirrors: {}\n"
        "pdk_digests: {sky130A: sha256:p}\n"
        "stale_source_policy: {grace_period_hours: 24, action_on_failure: ci_red}\n"
        "ci_verification: {last_green_commit: g, last_green_at: '2026-04-20T00:00:00Z'}\n"
    )
    result = CliRunner().invoke(
        main, ["lockfile-verify", "--lockfile", str(lock), "--scope", "l1"],
    )
    assert result.exit_code == 0
    assert '"verified": true' in result.output
    assert '"scope": "l1"' in result.output


def test_auth_login_calls_aws_sso():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 0
        result = CliRunner().invoke(main, ["auth", "login"])
    assert result.exit_code == 0
    run_mock.assert_called_once_with(
        ["aws", "sso", "login", "--profile", "semi-design-operator"],
        check=False,
    )


def test_auth_login_propagates_nonzero_returncode():
    with patch("subprocess.run") as run_mock:
        run_mock.return_value.returncode = 2
        result = CliRunner().invoke(main, ["auth", "login"])
    assert result.exit_code == 2


def test_lockfile_verify_fails_when_l1_sha_null(tmp_path):
    lock = tmp_path / "lockfile.yaml"
    lock.write_text(
        "version: 1\n"
        "commit_shas:\n"
        "  openroad: null\n  librelane: def\n  yosys: ghi\n  open_pdks: jkl\n"
        "  verilator: null\n  cocotb: null\n  chipyard: null\n"
        "  gemmini: null\n  mlcommons_tiny: null\n"
        "container_digests:\n"
        "  orfs-runner: sha256:x\n  librelane-runner: sha256:y\n"
        "  metric-collector: sha256:z\n"
        "pdk_digests: {sky130A: sha256:p}\n"
    )
    result = CliRunner().invoke(
        main, ["lockfile-verify", "--lockfile", str(lock), "--scope", "l1"],
    )
    assert result.exit_code == 1
    assert '"verified": false' in result.output
