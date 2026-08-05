from app.brain.ontology.models import (
    UniversalEvent,
    UniversalObjectRef,
    ValueMeasure,
)
from app.brain.ontology.transitions import UniversalTransition


def make_event(**overrides):
    values = {
        "object": UniversalObjectRef(kind="commitment", label="Example"),
        "intent": "observation",
        "transition": UniversalTransition.OBSERVED,
        "state": "observed",
        "world": "business",
        "confidence": 0.75,
        "source": "test",
    }
    values.update(overrides)
    return UniversalEvent(**values)


def test_object_ref_requires_kind_and_label():
    try:
        UniversalObjectRef(kind="", label="Example")
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        UniversalObjectRef(kind="document", label="")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_confidence_must_be_in_range():
    try:
        make_event(confidence=1.1)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    try:
        make_event(confidence=-0.1)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_terminal_transition_closes_event():
    event = make_event(
        transition=UniversalTransition.CLOSED,
        state="closed",
    )
    assert event.is_closed is True
    assert event.closure == "closed"


def test_non_terminal_transition_remains_open():
    event = make_event(
        transition=UniversalTransition.STARTED,
        state="started",
    )
    assert event.is_closed is False
    assert event.closure == "open"


def test_value_measure_validates_importance():
    measure = ValueMeasure(
        amount=250000.0,
        currency="INR",
        importance=90,
    )
    assert measure.amount == 250000.0

    try:
        ValueMeasure(importance=101)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_event_serialization_uses_string_transitions():
    event = make_event(
        expected_next=UniversalTransition.RECEIVED,
        value=ValueMeasure(quantity=12.5, unit="km"),
    )

    data = event.to_dict()

    assert data["transition"] == "observed"
    assert data["expected_next"] == "received"
    assert data["value"]["quantity"] == 12.5
    assert data["event_id"]
