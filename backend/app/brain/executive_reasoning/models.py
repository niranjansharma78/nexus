from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

class DecisionKind(StrEnum):
    ACTION = "action"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    INFORMATION = "information"

class DecisionStatus(StrEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REFLECTED = "reflected"

@dataclass(slots=True)
class UniversalDecision:
    title: str
    kind: DecisionKind
    priority: float
    confidence: float
    importance: float
    urgency: float
    why_now: str
    recommended_action: str | None = None
    delegation_target: str | None = None
    expected_impact: str | None = None
    related_event_ids: list[str] = field(default_factory=list)
    related_learning_ids: list[str] = field(default_factory=list)
    related_question_ids: list[str] = field(default_factory=list)
    evidence_ids: list[int] = field(default_factory=list)
    status: DecisionStatus = DecisionStatus.NEW
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip(): raise ValueError("Decision title is required")
        if not self.why_now.strip(): raise ValueError("why_now is required")
        for name, value in {"priority":self.priority,"confidence":self.confidence,"importance":self.importance,"urgency":self.urgency}.items():
            if not 0.0 <= float(value) <= 1.0: raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["status"] = self.status.value
        return data
