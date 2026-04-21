"""JSONL trace logger for infrastructure-level events.

Kept separate from L3 reasoning traces (which are a novelty artifact of the
research, see overview spec §4.3). This file logs boto3 calls, SFN state
transitions, and lifecycle events — strictly for debugging.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self, trace_dir: Path, run_id: str) -> None:
        trace_dir.mkdir(parents=True, exist_ok=True)
        self._path = trace_dir / f"{run_id}.jsonl"

    def emit(self, *, event: str, payload: dict[str, Any]) -> None:
        line = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self._path.open("a") as fh:
            fh.write(json.dumps(line) + "\n")
