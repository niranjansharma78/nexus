from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class OrchestrationRequest:
    objective: str
    world: str | None = None
    intent: str | None = None
    context_query: str | None = None
    prediction_inputs: list[dict[str, Any]] = field(default_factory=list)
    simulation_options: list[dict[str, Any]] = field(default_factory=list)
    decision_options: list[dict[str, Any]] = field(default_factory=list)
    plan_tasks: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")


@dataclass(slots=True)
class OrchestrationResult:
    objective: str
    orchestration_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None
    context: dict[str, Any] | None = None
    predictions: list[dict[str, Any]] = field(default_factory=list)
    simulation: dict[str, Any] | None = None
    decision: dict[str, Any] | None = None
    plan: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

    def finish(self) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["succeeded"] = self.succeeded
        return data
