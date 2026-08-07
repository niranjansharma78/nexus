from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

class PredictionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class PredictionOutcome(StrEnum):
    OCCURRED = "occurred"
    DID_NOT_OCCUR = "did_not_occur"
    PARTIAL = "partial"
    UNKNOWN = "unknown"

@dataclass(slots=True)
class Prediction:
    target: str
    prediction_type: str
    probability: float
    confidence: float
    horizon: str
    expected_by: str | None = None
    rationale: str = ""
    assumptions: list[str] = field(default_factory=list)
    evidence_ids: list[int] = field(default_factory=list)
    related_event_ids: list[str] = field(default_factory=list)
    world: str | None = None
    prediction_id: str = field(default_factory=lambda: str(uuid4()))
    status: PredictionStatus = PredictionStatus.OPEN
    outcome: PredictionOutcome | None = None
    resolved_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target.strip() or not self.prediction_type.strip() or not self.horizon.strip():
            raise ValueError("target, prediction_type and horizon are required")
        if not 0.0 <= float(self.probability) <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["outcome"] = self.outcome.value if self.outcome else None
        return data
