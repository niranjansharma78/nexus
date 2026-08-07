from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

class ContextKind(StrEnum):
    EVENT = "event"
    LEARNING = "learning"
    QUESTION = "question"

@dataclass(slots=True, frozen=True)
class ContextItem:
    kind: ContextKind
    reference_id: str
    label: str
    relevance: float
    confidence: float
    occurred_at: str | None = None
    world: str | None = None
    source: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.reference_id.strip() or not self.label.strip():
            raise ValueError("reference_id and label are required")
        if not 0 <= self.relevance <= 1 or not 0 <= self.confidence <= 1:
            raise ValueError("scores must be between 0 and 1")

    def to_dict(self):
        data = asdict(self)
        data["kind"] = self.kind.value
        return data

@dataclass(slots=True)
class WorkingContext:
    query: str
    items: list[ContextItem] = field(default_factory=list)
    world: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "query": self.query,
            "items": [item.to_dict() for item in self.items],
            "world": self.world,
            "summary": self.summary,
        }
