from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

class LearningDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass(slots=True, frozen=True)
class RelationshipObservation:
    source_label: str
    target_label: str
    relation: str
    confidence: float
    evidence_id: int | None = None
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_label.strip() or not self.target_label.strip() or not self.relation.strip():
            raise ValueError("Source, target and relation are required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")

@dataclass(slots=True)
class LearningCandidate:
    source_label: str
    target_label: str
    relation: str
    evidence_count: int
    confidence: float
    first_seen: str
    last_seen: str
    candidate_id: str = field(default_factory=lambda: str(uuid4()))
    decision: LearningDecision = LearningDecision.PENDING
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.evidence_count < 1:
            raise ValueError("Evidence count must be at least 1")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        return data
