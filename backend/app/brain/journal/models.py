from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class BrainJournalMetric:
    name: str
    value: float
    unit: str | None = None
    previous_value: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Metric name is required")

    @property
    def delta(self) -> float | None:
        if self.previous_value is None:
            return None
        return round(self.value - self.previous_value, 10)


@dataclass(slots=True, frozen=True)
class BrainJournalLearning:
    category: str
    statement: str
    confidence: float
    evidence_count: int = 0

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("Learning category is required")
        if not self.statement.strip():
            raise ValueError("Learning statement is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Learning confidence must be between 0 and 1")
        if self.evidence_count < 0:
            raise ValueError("Evidence count cannot be negative")


@dataclass(slots=True)
class BrainJournalEntry:
    journal_date: str
    scope: str
    summary: str
    metrics: list[BrainJournalMetric] = field(default_factory=list)
    learnings: list[BrainJournalLearning] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    journal_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        date.fromisoformat(self.journal_date)
        if not self.scope.strip():
            raise ValueError("Journal scope is required")
        if not self.summary.strip():
            raise ValueError("Journal summary is required")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for metric, source in zip(data["metrics"], self.metrics):
            metric["delta"] = source.delta
        return data
