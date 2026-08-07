from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class ObservationStatus(StrEnum):
    NEW = "new"
    NORMALIZED = "normalized"
    REJECTED = "rejected"


class SensorHealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    DISABLED = "disabled"


@dataclass(slots=True, frozen=True)
class Observation:
    sensor_id: str
    source: str
    observed_at: str
    raw_payload: dict[str, Any]
    confidence: float = 1.0
    observation_id: str = field(default_factory=lambda: str(uuid4()))
    status: ObservationStatus = ObservationStatus.NEW
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError("sensor_id is required")
        if not self.source.strip():
            raise ValueError("source is required")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(slots=True, frozen=True)
class UniversalEvidence:
    connector: str
    evidence_type: str
    observed_at: str
    source: str
    payload: dict[str, Any]
    confidence: float
    evidence_uid: str = field(default_factory=lambda: str(uuid4()))
    author: str | None = None
    attachments: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.connector.strip():
            raise ValueError("connector is required")
        if not self.evidence_type.strip():
            raise ValueError("evidence_type is required")
        if not self.source.strip():
            raise ValueError("source is required")
        datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["attachments"] = list(self.attachments)
        return data


@dataclass(slots=True, frozen=True)
class SensorHealth:
    sensor_id: str
    state: SensorHealthState
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    message: str = ""
    last_success_at: str | None = None
    records_processed: int = 0
    latency_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError("sensor_id is required")
        datetime.fromisoformat(self.checked_at.replace("Z", "+00:00"))
        if self.records_processed < 0:
            raise ValueError("records_processed cannot be negative")
