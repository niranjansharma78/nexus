from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class RuntimeTrigger(StrEnum):
    MANUAL = "manual"
    EVIDENCE = "evidence"
    EVENT = "event"
    SCHEDULE = "schedule"


@dataclass(slots=True)
class RuntimeRunResult:
    trigger: RuntimeTrigger
    objective: str
    run_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: str | None = None
    orchestration: dict[str, Any] | None = None
    policy: dict[str, Any] = field(default_factory=dict)
    requires_human_approval: bool = True
    errors: list[str] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def finish(self) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["trigger"] = self.trigger.value
        data["succeeded"] = self.succeeded
        return data
