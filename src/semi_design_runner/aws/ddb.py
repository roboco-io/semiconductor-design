"""DynamoDB wrappers. Candidates.ddb_write_count is the app-level counter
used by KG-E (spec §6.2). Every candidate write increments it atomically so
post-run assertions do not depend on CloudWatch attribution."""

from __future__ import annotations

from typing import Any


def put_candidate_with_count(
    client: Any,
    *,
    table: str,
    run_id: str,
    gen: int,
    cand: int,
    attributes: dict[str, Any],
) -> None:
    client.update_item(
        TableName=table,
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": f"gen#{gen}#cand#{cand}"},
        },
        UpdateExpression="SET #a = :a ADD ddb_write_count :one",
        ExpressionAttributeNames={"#a": "attributes"},
        ExpressionAttributeValues={
            ":a": {"M": {k: {"S": str(v)} for k, v in attributes.items()}},
            ":one": {"N": "1"},
        },
    )


def get_ddb_write_count(
    client: Any,
    *,
    table: str,
    run_id: str,
    gen: int,
    cand: int,
) -> int:
    resp = client.get_item(
        TableName=table,
        Key={
            "run_id": {"S": run_id},
            "gen_cand": {"S": f"gen#{gen}#cand#{cand}"},
        },
        ProjectionExpression="ddb_write_count",
    )
    item = resp.get("Item")
    if not item or "ddb_write_count" not in item:
        return 0
    return int(item["ddb_write_count"]["N"])
