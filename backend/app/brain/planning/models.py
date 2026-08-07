from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class PlanTask:
    title: str
    owner: str | None = None
    due_at: str | None = None
    duration_hours: float = 1.0
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: float = 0.5
    progress: float = 0.0
    task_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("task title is required")
        if self.duration_hours < 0:
            raise ValueError("duration_hours cannot be negative")
        if not 0.0 <= float(self.priority) <= 1.0:
            raise ValueError("priority must be between 0 and 1")
        if not 0.0 <= float(self.progress) <= 1.0:
            raise ValueError("progress must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(slots=True)
class Plan:
    objective: str
    tasks: list[PlanTask]
    world: str | None = None
    decision_refs: list[str] = field(default_factory=list)
    simulation_refs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    status: PlanStatus = PlanStatus.DRAFT
    progress: float = 0.0
    critical_path: list[str] = field(default_factory=list)
    replanning_required: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not self.tasks:
            raise ValueError("At least one task is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["tasks"] = [task.to_dict() for task in self.tasks]
        return data
