"""L2.memory.recall output schema.

L1.run / L3.agent decision input schemas MUST NOT import L2RecallNode
or any of its confidence* / source_* / valid_* fields.
See L2 derived spec §3.3 #5 (confidence isolation rule).
"""

from __future__ import annotations

from typing import Literal, Optional, TypeAlias

from pydantic import BaseModel, ConfigDict


class L2RecallNode(BaseModel):
    """Single node returned by L2.memory.recall().

    Parent-required fields (node_id, label, source_file, tier) mirror the L2
    graph index. The 9 optional fields extend recall output per spec §5.2:

    - Provenance: source_files, source_count — which wiki/raw entries back
      this node (Alternative B tier × source_count → GOLD/SILVER/BRONZE mapping).
    - Claim strength: confidence (graded) + confidence_score (raw float driving
      the grade). confidence is None for AMBIGUOUS tier per §3.2 last row.
    - Freshness: last_ingested / valid_from / valid_to are ISO-8601 strings;
      age_days is the derived integer for agent cutoff logic (§4).
    """

    model_config = ConfigDict(extra="forbid")

    node_id: str
    label: str
    source_file: str
    tier: Literal["EXTRACTED", "INFERRED", "AMBIGUOUS"]

    snippet: Optional[str] = None

    # Provenance (ADDED §5.2)
    source_files: Optional[list[str]] = None
    source_count: Optional[int] = None

    # Claim strength (ADDED §5.2). confidence None when tier=AMBIGUOUS (§3.2).
    confidence: Optional[Literal["GOLD", "SILVER", "BRONZE"]] = None
    confidence_score: Optional[float] = None

    # Freshness (ADDED §5.2, §4). ISO-8601 string convention — no datetime
    # parsing to avoid timezone-normalization drift between recall callers.
    last_ingested: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    age_days: Optional[int] = None


L2RecallResponse: TypeAlias = list[L2RecallNode]
