from pathlib import Path

from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)
from app.brain.runtime.service import BrainRuntime


def test_empty_runtime_cycle_completes(tmp_path: Path):
    result = BrainRuntime(tmp_path / "brain.db").run_cycle(
        journal_date="2026-08-06"
    )

    assert result.finished_at is not None
    assert result.events_seen == 0
    assert result.journal_written is True
    assert result.decisions_created == 0
    assert result.succeeded is True


def test_runtime_generates_decision_from_open_event(tmp_path: Path):
    database = tmp_path / "brain.db"
    UniversalEventRepository(database).save(
        UniversalEvent(
            event_id="event-1",
            object=UniversalObjectRef(
                kind="commitment",
                label="Customer request",
            ),
            intent="request",
            transition=UniversalTransition.REQUESTED,
            state="requested",
            world="business",
            confidence=0.85,
            source="test",
        )
    )

    result = BrainRuntime(database).run_cycle(
        journal_date="2026-08-06"
    )

    assert result.events_seen == 1
    assert result.decisions_created >= 1
    assert result.journal_written is True
    assert result.details["executive_brief"]["decisions"]


def test_runtime_reports_failures_without_crashing(tmp_path: Path):
    runtime = BrainRuntime(tmp_path / "brain.db")

    def broken_list(*args, **kwargs):
        raise RuntimeError("simulated failure")

    runtime.event_repository.list = broken_list

    result = runtime.run_cycle(journal_date="2026-08-06")

    assert result.finished_at is not None
    assert any(
        item.startswith("event_read_failed:")
        for item in result.errors
    )
