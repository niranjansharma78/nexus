from __future__ import annotations

from datetime import date
from pathlib import Path

from app.brain.core.context import BrainContextBuilder
from app.brain.curiosity.service import CuriosityEngine
from app.brain.executive_reasoning.service import ExecutiveReasoningEngine
from app.brain.journal.service import BrainJournalService
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)

from .models import RuntimeCycleResult


class BrainRuntime:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.event_repository = UniversalEventRepository(self.database_path)
        self.curiosity_engine = CuriosityEngine(self.database_path)
        self.journal_service = BrainJournalService(self.database_path)
        self.context_builder = BrainContextBuilder(self.database_path)
        self.reasoning_engine = ExecutiveReasoningEngine()

    def run_cycle(
        self,
        *,
        journal_date: str | None = None,
        scope: str = "organization",
        event_limit: int = 500,
        brief_limit: int = 10,
    ) -> RuntimeCycleResult:
        result = RuntimeCycleResult()

        try:
            events = self.event_repository.list(limit=event_limit)
            result.events_seen = len(events)
        except Exception as exc:
            result.errors.append(f"event_read_failed: {exc}")
            events = []

        try:
            questions = self.curiosity_engine.discover_from_events(
                limit=event_limit
            )
            result.curiosity_questions_created = len(questions)
        except Exception as exc:
            result.errors.append(f"curiosity_failed: {exc}")

        try:
            self.journal_service.build_daily_entry(
                journal_date=journal_date or date.today().isoformat(),
                scope=scope,
            )
            result.journal_written = True
        except Exception as exc:
            result.errors.append(f"journal_failed: {exc}")

        try:
            context = self.context_builder.build(
                event_limit=event_limit,
            )
            brief = self.reasoning_engine.executive_brief(
                context,
                limit=brief_limit,
            )
            result.decisions_created = int(
                brief["summary"]["decision_count"]
            )
            result.brain_confidence = float(
                brief["summary"]["brain_confidence"]
            )
            result.brain_confidence_band = str(
                brief["summary"]["brain_confidence_band"]
            )
            result.details["executive_brief"] = brief
        except Exception as exc:
            result.errors.append(f"reasoning_failed: {exc}")

        result.details["event_ids"] = [
            event.event_id for event in events[:50]
        ]
        result.finish()
        return result
