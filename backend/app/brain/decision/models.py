from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CLOSED = "closed"


@dataclass(slots=True)
class DecisionOption:
    option_id: str
    label: str
    expected_value: float
    expected_risk: float
    confidence: float
    reversibility: float = 0.5
    cost_score: float = 0.0
    complexity_score: float = 0.0
    constraint_violations: list[str] = field(default_factory=list)
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.option_id.strip():
            raise ValueError("option_id is required")
        if not self.label.strip():
            raise ValueError("label is required")
        for name, value in {
            "expected_value": self.expected_value,
            "expected_risk": self.expected_risk,
            "confidence": self.confidence,
            "reversibility": self.reversibility,
            "cost_score": self.cost_score,
            "complexity_score": self.complexity_score,
        }.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionRecord:
    objective: str
    options: list[DecisionOption]
    recommended_option_id: str | None
    ranking: list[dict[str, Any]]
    confidence: float
    rationale: str
    world: str | None = None
    intent: str | None = None
    context_summary: dict[str, Any] = field(default_factory=dict)
    prediction_refs: list[str] = field(default_factory=list)
    simulation_refs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    chosen_option_id: str | None = None
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    status: DecisionStatus = DecisionStatus.PROPOSED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not self.options:
            raise ValueError("At least one option is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["options"] = [item.to_dict() for item in self.options]
        return data
