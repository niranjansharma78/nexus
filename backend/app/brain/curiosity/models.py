from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class CuriosityStatus(StrEnum):
    OPEN = "open"
    ANSWERED = "answered"
    DISMISSED = "dismissed"


@dataclass(slots=True)
class CuriosityQuestion:
    question: str
    reason: str
    priority: int
    confidence: float
    scope: str = "organization"
    related_event_id: str | None = None
    related_evidence_id: int | None = None
    question_id: str = field(default_factory=lambda: str(uuid4()))
    status: CuriosityStatus = CuriosityStatus.OPEN
    answer: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("Question is required")
        if not self.reason.strip():
            raise ValueError("Reason is required")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be between 1 and 100")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
