"""데이터셋 조립 + manifest + I/O (flow_lockfile_sha 재현성 앵커)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def flow_lockfile_sha(lockfile_path: str | Path) -> str:
    return hashlib.sha256(Path(lockfile_path).read_bytes()).hexdigest()
