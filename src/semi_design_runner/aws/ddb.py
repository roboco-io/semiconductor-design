"""DynamoDB wrappers. Candidates.ddb_write_count is the app-level counter
used by KG-E (spec §6.2). Every candidate write increments it atomically so
post-run assertions do not depend on CloudWatch attribution."""

from __future__ import annotations

from typing import Any


def _to_attr_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"BOOL": value}
    if isinstance(value, int | float):
        return {"N": str(value)}
    return {"S": str(value)}


def put_candidate_with_count(
    client: Any,
    *,
    table: str,
    run_id: str,
    gen: int,
    cand: int,
    attributes: dict[str, Any],
) -> None:
    names = {f"#{k}": k for k in attributes}
    values = {f":{k}": _to_attr_value(v) for k, v in attributes.items()}
    set_expr = ", ".join(f"#{k} = :{k}" for k in attributes)
    update_expr = f"SET {set_expr} ADD ddb_write_count :one" if set_expr else "ADD ddb_write_count :one"
    values[":one"] = {"N": "1"}

    kwargs: dict[str, Any] = {
        "TableName": table,
        "Key": {
            "run_id": {"S": run_id},
            "gen_cand": {"S": f"gen#{gen}#cand#{cand}"},
        },
        "UpdateExpression": update_expr,
        "ExpressionAttributeValues": values,
    }
    if names:
        kwargs["ExpressionAttributeNames"] = names

    client.update_item(
        **kwargs,
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
