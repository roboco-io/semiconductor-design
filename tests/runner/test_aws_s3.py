from datetime import datetime, timezone
from unittest.mock import MagicMock

from semi_design_runner.aws.s3 import download_final, put_spec, put_with_retention


def test_put_with_retention_sets_governance_mode_and_date():
    client = MagicMock()
    put_with_retention(
        client,
        bucket="b",
        key="runs/r/final/m.json",
        body=b"{}",
        retention_days=30,
    )
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "b"
    assert kwargs["Key"] == "runs/r/final/m.json"
    assert kwargs["Body"] == b"{}"
    assert kwargs["ObjectLockMode"] == "GOVERNANCE"
    assert isinstance(kwargs["ObjectLockRetainUntilDate"], datetime)
    delta = kwargs["ObjectLockRetainUntilDate"] - datetime.now(tz=timezone.utc)
    assert 29 <= delta.days <= 30


def test_put_spec_writes_to_staging_returns_uri():
    client = MagicMock()
    uri = put_spec(client, bucket="bkt", run_id="abc", spec_yaml="version: 1")
    assert uri == "s3://bkt/runs/abc/staging/spec.yaml"
    client.put_object.assert_called_once()


def test_download_final_mirrors_prefix(tmp_path):
    client = MagicMock()
    paginator = MagicMock()
    client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "runs/abc/final/metrics.json"},
                {"Key": "runs/abc/final/signoff/sta.rpt"},
            ]
        },
    ]
    download_final(client, bucket="bkt", run_id="abc", dest=tmp_path)
    assert client.download_file.call_count == 2
    # relative paths mirrored under dest
    assert (tmp_path / "signoff").exists()
