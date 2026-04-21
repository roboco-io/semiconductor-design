import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from semi_design_runner.cli import main


def test_submit_starts_execution_and_prints_arn():
    with (
        patch("semi_design_runner.cli.make_client") as mk,
        patch("semi_design_runner.cli.start_execution", return_value="arn:e:abc"),
    ):
        mk.return_value = object()
        result = CliRunner().invoke(
            main,
            ["submit", "--run-id", "abc", "--state-machine-arn", "arn:sm"],
        )
    assert result.exit_code == 0
    assert "arn:e:abc" in result.output


def test_status_joins_ddb_and_sfn():
    ddb = MagicMock()
    ddb.get_item.return_value = {"Item": {"status": {"S": "clean"}}}
    sfn = MagicMock()
    sfn.describe_execution.return_value = {"status": "SUCCEEDED"}
    with patch(
        "semi_design_runner.cli.make_client",
        side_effect=lambda svc, **kw: {"dynamodb": ddb, "stepfunctions": sfn}[svc],
    ):
        result = CliRunner().invoke(
            main,
            ["status", "--run-id", "r1", "--execution-arn", "arn:e"],
        )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ddb_status"] == "clean"
    assert payload["sfn_status"] == "SUCCEEDED"
    # Lock in the reserved-word alias: `status` is a DDB reserved keyword.
    get_item_kwargs = ddb.get_item.call_args.kwargs
    assert get_item_kwargs["ProjectionExpression"] == "#s"
    assert get_item_kwargs["ExpressionAttributeNames"] == {"#s": "status"}


def test_artifacts_downloads_final_prefix(tmp_path):
    with (
        patch("semi_design_runner.cli.make_client") as mk,
        patch("semi_design_runner.cli.download_final") as dl,
    ):
        mk.return_value = object()
        result = CliRunner().invoke(
            main,
            ["artifacts", "--run-id", "r1", "--bucket", "b", "--dest", str(tmp_path)],
        )
    assert result.exit_code == 0
    dl.assert_called_once()
    kwargs = dl.call_args.kwargs
    assert kwargs["bucket"] == "b"
    assert kwargs["run_id"] == "r1"
    assert kwargs["dest"] == tmp_path


def test_cost_emits_budget_guard_check():
    ddb = MagicMock()
    ddb.get_item.return_value = {"Item": {"total_cost_usd": {"N": "4.2"}}}
    with patch("semi_design_runner.cli.make_client", return_value=ddb):
        result = CliRunner().invoke(main, ["cost", "--run-id", "r1"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total_cost_usd"] == 4.2
