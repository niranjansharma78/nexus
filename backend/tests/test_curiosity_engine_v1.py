from pathlib import Path

from app.brain.curiosity.models import CuriosityStatus
from app.brain.curiosity.service import CuriosityEngine
from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import UniversalEventRepository


def save_event(
    db: Path,
    *,
    event_id: str,
    transition: UniversalTransition,
    confidence: float,
    expected_next=None,
    counterparty=None,
    kind="event",
):
    repo = UniversalEventRepository(db)
    repo.save(
        UniversalEvent(
            event_id=event_id,
            object=UniversalObjectRef(kind=kind, label=event_id),
            intent="observation",
            transition=transition,
            state=transition.value,
            world="business",
            confidence=confidence,
            source="test",
            expected_next=expected_next,
            counterparty=counterparty,
        )
    )


def test_low_confidence_observation_creates_question(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(
        db,
        event_id="unknown",
        transition=UniversalTransition.OBSERVED,
        confidence=0.4,
    )
    items = CuriosityEngine(db).discover_from_events()
    assert any("What does" in item.question for item in items)


def test_open_event_without_next_creates_question(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(
        db,
        event_id="open-item",
        transition=UniversalTransition.STARTED,
        confidence=0.8,
    )
    items = CuriosityEngine(db).discover_from_events()
    assert any("What should normally happen" in item.question for item in items)


def test_missing_counterparty_creates_high_priority_question(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(
        db,
        event_id="commitment-1",
        transition=UniversalTransition.REQUESTED,
        confidence=0.8,
        kind="commitment",
    )
    items = CuriosityEngine(db).discover_from_events()
    assert any(item.priority == 80 for item in items)


def test_question_can_be_answered_and_dismissed(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(
        db,
        event_id="unknown",
        transition=UniversalTransition.OBSERVED,
        confidence=0.4,
    )
    engine = CuriosityEngine(db)
    question = engine.discover_from_events()[0]
    answered = engine.repository.answer(question.question_id, "It is a supplier enquiry.")
    assert answered.status == CuriosityStatus.ANSWERED
    assert answered.answer == "It is a supplier enquiry."

    dismissed = engine.repository.dismiss(question.question_id)
    assert dismissed.status == CuriosityStatus.DISMISSED
