from pathlib import Path

from app.brain.journal.models import (
    BrainJournalEntry,
    BrainJournalLearning,
    BrainJournalMetric,
)
from app.brain.journal.repository import BrainJournalRepository
from app.brain.journal.service import BrainJournalService
from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)


def make_event(event_id: str, transition: UniversalTransition):
    return UniversalEvent(
        event_id=event_id,
        object=UniversalObjectRef(kind="event", label=event_id),
        intent="observation",
        transition=transition,
        state=transition.value,
        world="business",
        confidence=0.8,
        source="test",
    )


def test_metric_delta():
    metric = BrainJournalMetric(
        name="confidence",
        value=0.8,
        previous_value=0.7,
    )
    assert metric.delta == 0.1


def test_journal_entry_round_trip(tmp_path: Path):
    repo = BrainJournalRepository(tmp_path / "brain.db")
    entry = BrainJournalEntry(
        journal_date="2026-08-05",
        scope="organization",
        summary="Daily summary",
        metrics=[BrainJournalMetric(name="events", value=5)],
        learnings=[
            BrainJournalLearning(
                category="pattern",
                statement="A pattern was observed.",
                confidence=0.8,
                evidence_count=3,
            )
        ],
        corrections=["Corrected one classification"],
        open_questions=["Confirm one relationship"],
    )

    repo.save(entry)
    loaded = repo.get("organization", "2026-08-05")

    assert loaded is not None
    assert loaded.summary == "Daily summary"
    assert loaded.metrics[0].name == "events"
    assert loaded.learnings[0].evidence_count == 3
    assert loaded.corrections == ["Corrected one classification"]


def test_same_scope_and_date_is_updated(tmp_path: Path):
    repo = BrainJournalRepository(tmp_path / "brain.db")

    first = BrainJournalEntry(
        journal_date="2026-08-05",
        scope="organization",
        summary="First",
    )
    second = BrainJournalEntry(
        journal_date="2026-08-05",
        scope="organization",
        summary="Second",
    )

    repo.save(first)
    repo.save(second)

    items = repo.list(scope="organization")
    assert len(items) == 1
    assert items[0].summary == "Second"


def test_service_builds_daily_entry_from_universal_events(tmp_path: Path):
    database = tmp_path / "brain.db"
    event_repo = UniversalEventRepository(database)

    event_repo.save(make_event("a", UniversalTransition.REQUESTED))
    event_repo.save(make_event("b", UniversalTransition.CLOSED))

    service = BrainJournalService(database)
    entry = service.build_daily_entry(
        journal_date="2026-08-05",
        previous_confidence=0.7,
        corrections=["Corrected duplicate event"],
        open_questions=["Confirm counterparty"],
    )

    metrics = {item.name: item for item in entry.metrics}

    assert metrics["events_reviewed"].value == 2
    assert metrics["open_events"].value == 1
    assert metrics["closed_events"].value == 1
    assert metrics["average_confidence"].value == 0.8
    assert metrics["average_confidence"].delta == 0.1
    assert entry.corrections == ["Corrected duplicate event"]
    assert entry.open_questions == ["Confirm counterparty"]
    assert entry.learnings


def test_invalid_learning_confidence_is_rejected():
    try:
        BrainJournalLearning(
            category="pattern",
            statement="Invalid",
            confidence=1.2,
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass
