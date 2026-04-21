"""boto3 session + client factory with SSO profile and adaptive retries."""
from __future__ import annotations

import boto3
from botocore.config import Config

_DEFAULT_RETRY_CONFIG = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},
)


def make_session(profile: str | None = "semi-design-operator") -> boto3.Session:
    return boto3.Session(profile_name=profile)


def make_client(service: str, *, profile: str | None = "semi-design-operator"):
    session = make_session(profile=profile)
    return session.client(service, config=_DEFAULT_RETRY_CONFIG)
