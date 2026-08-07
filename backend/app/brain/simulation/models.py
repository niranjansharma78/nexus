from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class SimulationStatus(StrEnum):
    CREATED = "created"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class SimulationOutcome:
    label: str
    probability: float
    value_score: float
    risk_score: float
    confidence: float
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("Outcome label is required")
        for name, value in {
            "probability": self.probability,
            "value_score": self.value_score,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
        }.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SimulationOption:
    option_id: str
    label: str
    outcomes: list[SimulationOutcome] = field(default_factory=list)
    cost_score: float = 0.0
    complexity_score: float = 0.0
    reversibility: float = 0.5
    constraint_violations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.option_id.strip():
            raise ValueError("option_id is required")
        if not self.label.strip():
            raise ValueError("Option label is required")
        for name, value in {
            "cost_score": self.cost_score,
            "complexity_score": self.complexity_score,
            "reversibility": self.reversibility,
        }.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["outcomes"] = [item.to_dict() for item in self.outcomes]
        return data


@dataclass(slots=True)
class Simulation:
    objective: str
    current_state: dict[str, Any]
    options: list[SimulationOption]
    horizon: str
    world: str | None = None
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    external_predictions: list[dict[str, Any]] = field(default_factory=list)
    simulation_id: str = field(default_factory=lambda: str(uuid4()))
    status: SimulationStatus = SimulationStatus.CREATED
    recommended_option_id: str | None = None
    ranking: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not self.horizon.strip():
            raise ValueError("horizon is required")
        if not self.options:
            raise ValueError("At least one option is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["options"] = [item.to_dict() for item in self.options]
        return data
