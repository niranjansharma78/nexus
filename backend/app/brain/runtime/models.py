from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class RuntimeCycleResult:
    cycle_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    finished_at: str | None = None
    events_seen: int = 0
    curiosity_questions_created: int = 0
    journal_written: bool = False
    decisions_created: int = 0
    brain_confidence: float = 0.0
    brain_confidence_band: str = "review"
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()

    @property
    def succeeded(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["succeeded"] = self.succeeded
        return data
