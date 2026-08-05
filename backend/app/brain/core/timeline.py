from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class TimelineItem:
    occurred_at: str
    kind: str
    label: str
    reference_id: str | None = None

    def __post_init__(self) -> None:
        datetime.fromisoformat(self.occurred_at.replace("Z", "+00:00"))
        if not self.kind.strip():
            raise ValueError("Timeline kind is required")
        if not self.label.strip():
            raise ValueError("Timeline label is required")
