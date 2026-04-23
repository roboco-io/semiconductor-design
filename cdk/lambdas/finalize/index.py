"""Finalize Lambda (L1 Process — WorkflowStack).

Per-object retention-aware finalization. L1 spec §4.3: every put/copy
into ``runs/{run_id}/final/`` MUST include ``x-amz-object-lock-mode=
GOVERNANCE`` and ``x-amz-object-lock-retain-until-date`` (= now + 90d) on
the same call. Writing ``_SUCCESS`` last is an invariant check — NOT a
locking step, and NOT a post-hoc batch lock (that is explicitly forbidden
by spec §4.3).
"""

from __future__ import annotations

import datetime
import os
from typing import Any

import boto3


BUCKET = os.environ["ARTIFACT_BUCKET"]
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "90"))

s3 = boto3.client("s3")


def _retention_args() -> dict[str, Any]:
    retain_until = datetime.datetime.now(
        tz=datetime.timezone.utc,
    ) + datetime.timedelta(days=RETENTION_DAYS)
    return {
        "ObjectLockMode": "GOVERNANCE",
        "ObjectLockRetainUntilDate": retain_until,
    }


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    run_id = event["run_id"]
    manifest: list[dict[str, str]] = event.get("manifest", [])
    for entry in manifest:
        s3.copy_object(
            Bucket=BUCKET,
            CopySource={"Bucket": BUCKET, "Key": entry["staging_key"]},
            Key=entry["final_key"],
            **_retention_args(),
        )
    # Sidecars — metrics, provenance, cost actuals — each with retention applied
    # on the same PutObject call.
    sidecars: dict[str, str] = event.get("sidecars", {})
    for sidecar_key, body_str in sidecars.items():
        s3.put_object(
            Bucket=BUCKET,
            Key=f"runs/{run_id}/final/{sidecar_key}",
            Body=body_str.encode(),
            **_retention_args(),
        )
    # _SUCCESS LAST — still with retention header. Order encodes the
    # "manifest complete" invariant.
    s3.put_object(
        Bucket=BUCKET,
        Key=f"runs/{run_id}/final/_SUCCESS",
        Body=b"",
        **_retention_args(),
    )
    return {"run_id": run_id, "status": "finalized"}
