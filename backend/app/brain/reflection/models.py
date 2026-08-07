from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ReflectionStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"


@dataclass(slots=True)
class ReflectionRecord:
    subject: str
    expected: str
    actual: str
    lesson: str
    confidence_before: float
    confidence_after: float
    world: str | None = None
    prediction_id: str | None = None
    simulation_id: str | None = None
    chosen_option_id: str | None = None
    recommended_option_id: str | None = None
    assumption_failures: list[str] = field(default_factory=list)
    evidence_ids: list[int] = field(default_factory=list)
    reflection_id: str = field(default_factory=lambda: str(uuid4()))
    status: ReflectionStatus = ReflectionStatus.COMPLETED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("subject is required")
        if not self.lesson.strip():
            raise ValueError("lesson is required")
        for name, value in {
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
        }.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def confidence_delta(self) -> float:
        return round(self.confidence_after - self.confidence_before, 10)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["confidence_delta"] = self.confidence_delta
        return data
