from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.brain.ontology.transitions import (
    UniversalTransition,
    is_terminal_transition,
)


@dataclass(slots=True, frozen=True)
class UniversalObjectRef:
    kind: str
    label: str
    external_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("Object kind is required")
        if not self.label.strip():
            raise ValueError("Object label is required")


@dataclass(slots=True, frozen=True)
class ValueMeasure:
    amount: float | None = None
    currency: str | None = None
    quantity: float | None = None
    unit: str | None = None
    importance: int | None = None

    def __post_init__(self) -> None:
        if self.importance is not None and not 0 <= self.importance <= 100:
            raise ValueError("Importance must be between 0 and 100")


@dataclass(slots=True)
class UniversalEvent:
    object: UniversalObjectRef
    intent: str
    transition: UniversalTransition
    state: str
    world: str
    confidence: float
    source: str

    actor: UniversalObjectRef | None = None
    counterparty: UniversalObjectRef | None = None
    value: ValueMeasure = field(default_factory=ValueMeasure)
    evidence_id: int | None = None
    expected_next: UniversalTransition | None = None
    closure: str = "open"
    organization_id: str | None = None
    domain_pack: str | None = None
    occurred_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.intent.strip():
            raise ValueError("Intent is required")
        if not self.state.strip():
            raise ValueError("State is required")
        if not self.world.strip():
            raise ValueError("World is required")
        if not self.source.strip():
            raise ValueError("Source is required")

        self.confidence = float(self.confidence)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")

        if is_terminal_transition(self.transition):
            self.closure = "closed"

    @property
    def is_closed(self) -> bool:
        return self.closure == "closed"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["transition"] = self.transition.value
        data["expected_next"] = (
            self.expected_next.value
            if self.expected_next is not None
            else None
        )
        return data
