from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AttentionPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFER = "defer"


@dataclass(slots=True)
class AttentionItem:
    label: str
    importance: float
    urgency: float
    novelty: float
    relevance: float
    risk: float
    confidence: float
    world: str | None = None
    source: str | None = None
    reference_id: str | None = None
    item_id: str = field(default_factory=lambda: str(uuid4()))
    attention_score: float = 0.0
    priority: AttentionPriority = AttentionPriority.LOW
    should_escalate: bool = False
    should_process_now: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label is required")
        for name, value in {
            "importance": self.importance,
            "urgency": self.urgency,
            "novelty": self.novelty,
            "relevance": self.relevance,
            "risk": self.risk,
            "confidence": self.confidence,
        }.items():
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["priority"] = self.priority.value
        return data
