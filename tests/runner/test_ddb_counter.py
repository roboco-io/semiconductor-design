from unittest.mock import MagicMock

from semi_design_runner.aws.ddb import get_ddb_write_count, put_candidate_with_count


def test_put_candidate_uses_add_to_increment_counter():
    client = MagicMock()
    put_candidate_with_count(
        client,
        table="Candidates",
        run_id="r1",
        gen=0,
        cand=3,
        attributes={"stage_status": "synth_ok"},
    )
    kwargs = client.update_item.call_args.kwargs
    assert kwargs["TableName"] == "Candidates"
    assert kwargs["Key"]["run_id"]["S"] == "r1"
    assert kwargs["Key"]["gen_cand"]["S"] == "gen#0#cand#3"
    assert "ADD ddb_write_count :one" in kwargs["UpdateExpression"]
    assert "SET #stage_status = :stage_status" in kwargs["UpdateExpression"]
    assert kwargs["ExpressionAttributeNames"]["#stage_status"] == "stage_status"
    assert kwargs["ExpressionAttributeValues"][":stage_status"] == {"S": "synth_ok"}
    assert kwargs["ExpressionAttributeValues"][":one"] == {"N": "1"}


def test_put_candidate_writes_status_as_top_level_reserved_attribute():
    client = MagicMock()
    put_candidate_with_count(
        client,
        table="Candidates",
        run_id="r1",
        gen=0,
        cand=0,
        attributes={"status": "in_progress"},
    )
    kwargs = client.update_item.call_args.kwargs
    assert kwargs["UpdateExpression"] == "SET #status = :status ADD ddb_write_count :one"
    assert kwargs["ExpressionAttributeNames"] == {"#status": "status"}
    assert kwargs["ExpressionAttributeValues"][":status"] == {"S": "in_progress"}


def test_get_counter_returns_zero_when_item_missing():
    client = MagicMock()
    client.get_item.return_value = {}
    assert (
        get_ddb_write_count(
            client,
            table="Candidates",
            run_id="r",
            gen=0,
            cand=0,
        )
        == 0
    )


def test_get_counter_returns_int_value():
    client = MagicMock()
    client.get_item.return_value = {"Item": {"ddb_write_count": {"N": "17"}}}
    assert (
        get_ddb_write_count(
            client,
            table="Candidates",
            run_id="r",
            gen=0,
            cand=0,
        )
        == 17
    )
