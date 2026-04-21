"""S3 operations for L1 runner.

`put_with_retention` implements the per-object retention pattern from spec §4.3:
GOVERNANCE-mode Object Lock is attached in the **same PutObject call** as the
data write, so there is no mutable-success window if finalize later fails.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def put_with_retention(
    client: Any,
    *,
    bucket: str,
    key: str,
    body: bytes,
    retention_days: int = 90,
) -> None:
    retain_until = datetime.now(tz=timezone.utc) + timedelta(days=retention_days)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ObjectLockMode="GOVERNANCE",
        ObjectLockRetainUntilDate=retain_until,
    )


def put_spec(client: Any, *, bucket: str, run_id: str, spec_yaml: str) -> str:
    """Write spec.yaml to staging prefix (no retention — staging is mutable)."""
    key = f"runs/{run_id}/staging/spec.yaml"
    client.put_object(Bucket=bucket, Key=key, Body=spec_yaml.encode())
    return f"s3://{bucket}/{key}"


def download_final(
    client: Any, *, bucket: str, run_id: str, dest: Path,
) -> None:
    """Download the final/ prefix mirror to local dest dir."""
    prefix = f"runs/{run_id}/final/"
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            rel = obj["Key"][len(prefix):]
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, obj["Key"], str(target))
