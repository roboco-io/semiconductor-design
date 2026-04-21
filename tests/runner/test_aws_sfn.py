import json
from unittest.mock import MagicMock
from semi_design_runner.aws.sfn import start_execution, describe_execution


def test_start_execution_serializes_payload_and_names_by_run_id():
    client = MagicMock()
    client.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123:execution:semi:r1",
    }
    arn = start_execution(
        client,
        state_machine_arn="arn:aws:states:us-east-1:123:stateMachine:semi",
        run_id="r1",
        input_payload={"spec_uri": "s3://b/spec.yaml", "seed": 42},
    )
    assert arn.endswith(":execution:semi:r1")
    kwargs = client.start_execution.call_args.kwargs
    assert kwargs["name"] == "r1"
    payload = json.loads(kwargs["input"])
    assert payload["spec_uri"] == "s3://b/spec.yaml"
    assert payload["seed"] == 42


def test_describe_execution_pass_through():
    client = MagicMock()
    client.describe_execution.return_value = {
        "status": "RUNNING",
        "startDate": "2026-04-21T00:00:00Z",
    }
    result = describe_execution(client, execution_arn="arn:e")
    assert result["status"] == "RUNNING"
    client.describe_execution.assert_called_once_with(executionArn="arn:e")
