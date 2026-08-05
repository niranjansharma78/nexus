from pathlib import Path

from app.brain.ontology.models import (
    UniversalEvent,
    UniversalObjectRef,
    ValueMeasure,
)
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)


def make_event(
    *,
    event_id: str,
    world: str = "business",
    transition: UniversalTransition = UniversalTransition.REQUESTED,
    evidence_id: int | None = 10,
) -> UniversalEvent:
    return UniversalEvent(
        event_id=event_id,
        object=UniversalObjectRef(
            kind="commitment",
            label=f"Event {event_id}",
        ),
        actor=UniversalObjectRef(
            kind="organization",
            label="Actor",
        ),
        counterparty=UniversalObjectRef(
            kind="organization",
            label="Counterparty",
        ),
        intent="request",
        transition=transition,
        state=transition.value,
        world=world,
        confidence=0.88,
        source="test",
        value=ValueMeasure(
            amount=250000.0,
            currency="INR",
            quantity=12.5,
            unit="km",
            importance=90,
        ),
        evidence_id=evidence_id,
        expected_next=UniversalTransition.COMMITTED,
        organization_id="org-1",
        domain_pack="generic",
        metadata={"example": True},
    )


def test_repository_round_trip(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")
    event = make_event(event_id="event-1")

    repository.save(event)
    loaded = repository.get("event-1")

    assert loaded is not None
    assert loaded.event_id == "event-1"
    assert loaded.object.label == "Event event-1"
    assert loaded.actor is not None
    assert loaded.actor.label == "Actor"
    assert loaded.counterparty is not None
    assert loaded.counterparty.label == "Counterparty"
    assert loaded.value.amount == 250000.0
    assert loaded.value.quantity == 12.5
    assert loaded.expected_next == UniversalTransition.COMMITTED
    assert loaded.metadata == {"example": True}


def test_repository_upsert_preserves_single_record(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")
    event = make_event(event_id="event-1")

    repository.save(event)
    event.state = "updated"
    event.confidence = 0.95
    repository.save(event)

    assert repository.count() == 1

    loaded = repository.get("event-1")
    assert loaded is not None
    assert loaded.state == "updated"
    assert loaded.confidence == 0.95


def test_repository_filters_by_world_closure_and_transition(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")

    repository.save(
        make_event(
            event_id="business-open",
            world="business",
            transition=UniversalTransition.REQUESTED,
        )
    )
    repository.save(
        make_event(
            event_id="family-closed",
            world="family",
            transition=UniversalTransition.CLOSED,
        )
    )

    business = repository.list(world="business")
    closed = repository.list(closure="closed")
    requested = repository.list(
        transition=UniversalTransition.REQUESTED
    )

    assert [item.event_id for item in business] == ["business-open"]
    assert [item.event_id for item in closed] == ["family-closed"]
    assert [item.event_id for item in requested] == ["business-open"]


def test_repository_filters_by_evidence_id(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")

    repository.save(make_event(event_id="a", evidence_id=21))
    repository.save(make_event(event_id="b", evidence_id=22))

    items = repository.list(evidence_id=22)

    assert [item.event_id for item in items] == ["b"]


def test_repository_delete_is_explicit(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")
    repository.save(make_event(event_id="event-1"))

    assert repository.delete("event-1") is True
    assert repository.get("event-1") is None
    assert repository.delete("event-1") is False


def test_repository_count_filters(tmp_path: Path):
    repository = UniversalEventRepository(tmp_path / "brain.db")

    repository.save(make_event(event_id="a", world="business"))
    repository.save(make_event(event_id="b", world="family"))
    repository.save(
        make_event(
            event_id="c",
            world="business",
            transition=UniversalTransition.CLOSED,
        )
    )

    assert repository.count() == 3
    assert repository.count(world="business") == 2
    assert repository.count(closure="closed") == 1
