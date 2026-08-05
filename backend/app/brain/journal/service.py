from __future__ import annotations

from datetime import date
from pathlib import Path

from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)

from .models import (
    BrainJournalEntry,
    BrainJournalLearning,
    BrainJournalMetric,
)
from .repository import BrainJournalRepository


class BrainJournalService:
    def __init__(
        self,
        database_path: str | Path,
    ) -> None:
        self.event_repository = UniversalEventRepository(database_path)
        self.journal_repository = BrainJournalRepository(database_path)

    def build_daily_entry(
        self,
        *,
        journal_date: str | None = None,
        scope: str = "organization",
        previous_confidence: float | None = None,
        corrections: list[str] | None = None,
        open_questions: list[str] | None = None,
    ) -> BrainJournalEntry:
        target_date = journal_date or date.today().isoformat()

        events = self.event_repository.list(limit=500)
        event_count = len(events)
        open_count = sum(1 for item in events if not item.is_closed)
        closed_count = sum(1 for item in events if item.is_closed)
        average_confidence = (
            sum(item.confidence for item in events) / event_count
            if event_count
            else 0.0
        )

        transition_counts: dict[str, int] = {}
        for event in events:
            key = event.transition.value
            transition_counts[key] = transition_counts.get(key, 0) + 1

        learnings: list[BrainJournalLearning] = []
        for transition, count in sorted(
            transition_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]:
            learnings.append(
                BrainJournalLearning(
                    category="pattern",
                    statement=(
                        f"Observed {count} event(s) in the "
                        f"'{transition}' transition."
                    ),
                    confidence=min(1.0, 0.5 + (count * 0.05)),
                    evidence_count=count,
                )
            )

        summary = (
            f"Nexus reviewed {event_count} universal event(s), "
            f"with {open_count} open and {closed_count} closed."
        )

        entry = BrainJournalEntry(
            journal_date=target_date,
            scope=scope,
            summary=summary,
            metrics=[
                BrainJournalMetric(
                    name="events_reviewed",
                    value=float(event_count),
                    unit="events",
                ),
                BrainJournalMetric(
                    name="open_events",
                    value=float(open_count),
                    unit="events",
                ),
                BrainJournalMetric(
                    name="closed_events",
                    value=float(closed_count),
                    unit="events",
                ),
                BrainJournalMetric(
                    name="average_confidence",
                    value=average_confidence,
                    unit="ratio",
                    previous_value=previous_confidence,
                ),
            ],
            learnings=learnings,
            corrections=corrections or [],
            open_questions=open_questions or [],
            metadata={
                "source": "universal_event_repository",
                "transition_counts": transition_counts,
            },
        )

        return self.journal_repository.save(entry)
