from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.brain.core.confidence import ConfidenceService
from app.brain.core.timeline import TimelineItem
from app.brain.curiosity.models import CuriosityStatus
from app.brain.curiosity.repository import CuriosityRepository
from app.brain.journal.repository import BrainJournalRepository
from app.brain.learning.models import LearningDecision
from app.brain.learning.repository import LearningRepository
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)


@dataclass(slots=True)
class BrainContext:
    events: list[dict[str, Any]] = field(default_factory=list)
    learnings: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[dict[str, Any]] = field(default_factory=list)
    journal_entries: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[TimelineItem] = field(default_factory=list)
    confidence: float = 0.0
    confidence_band: str = "review"
    summary: dict[str, Any] = field(default_factory=dict)


class BrainContextBuilder:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.event_repository = UniversalEventRepository(self.database_path)
        self.learning_repository = LearningRepository(self.database_path)
        self.curiosity_repository = CuriosityRepository(self.database_path)
        self.journal_repository = BrainJournalRepository(self.database_path)

    def build(
        self,
        *,
        event_limit: int = 100,
        learning_limit: int = 50,
        question_limit: int = 50,
        journal_limit: int = 7,
    ) -> BrainContext:
        events = self.event_repository.list(limit=event_limit)
        learnings = self.learning_repository.list(
            decision=LearningDecision.APPROVED,
            limit=learning_limit,
        )
        questions = self.curiosity_repository.list(
            status=CuriosityStatus.OPEN,
            limit=question_limit,
        )
        journals = self.journal_repository.list(limit=journal_limit)

        event_dicts = [event.to_dict() for event in events]
        learning_dicts = [item.to_dict() for item in learnings]
        question_dicts = [item.to_dict() for item in questions]
        journal_dicts = [entry.to_dict() for entry in journals]

        confidence_values = [event.confidence for event in events]
        confidence_values.extend(item.confidence for item in learnings)
        overall_confidence = ConfidenceService.average(confidence_values)

        timeline: list[TimelineItem] = [
            TimelineItem(
                occurred_at=event.occurred_at,
                kind="event",
                label=event.object.label,
                reference_id=event.event_id,
            )
            for event in events
        ]
        timeline.sort(key=lambda item: item.occurred_at, reverse=True)

        return BrainContext(
            events=event_dicts,
            learnings=learning_dicts,
            open_questions=question_dicts,
            journal_entries=journal_dicts,
            timeline=timeline,
            confidence=overall_confidence,
            confidence_band=ConfidenceService.band(overall_confidence),
            summary={
                "event_count": len(events),
                "approved_learning_count": len(learnings),
                "open_question_count": len(questions),
                "journal_entry_count": len(journals),
                "open_event_count": sum(1 for event in events if not event.is_closed),
                "closed_event_count": sum(1 for event in events if event.is_closed),
            },
        )
