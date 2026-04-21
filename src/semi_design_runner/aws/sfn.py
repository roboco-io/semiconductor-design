"""Step Functions wrappers. Execution name = run_id for easy tracing."""
from __future__ import annotations

import json
from typing import Any


def start_execution(
    client: Any,
    *,
    state_machine_arn: str,
    run_id: str,
    input_payload: dict[str, Any],
) -> str:
    resp = client.start_execution(
        stateMachineArn=state_machine_arn,
        name=run_id,
        input=json.dumps(input_payload),
    )
    return resp["executionArn"]


def describe_execution(client: Any, *, execution_arn: str) -> dict[str, Any]:
    return client.describe_execution(executionArn=execution_arn)
