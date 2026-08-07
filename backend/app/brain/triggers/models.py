from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class TriggerKind(StrEnum):
    EVIDENCE = "evidence"
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"


@dataclass(slots=True)
class TriggerEnvelope:
    kind: TriggerKind
    payload: dict[str, Any]
    world: str | None = None
    source: str | None = None
    objective: str | None = None
    trigger_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    fingerprint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        return data


@dataclass(slots=True)
class TriggerDispatchResult:
    trigger_id: str
    accepted: bool
    duplicate: bool = False
    runtime_run_id: str | None = None
    succeeded: bool = False
    errors: list[str] = field(default_factory=list)
    runtime_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
