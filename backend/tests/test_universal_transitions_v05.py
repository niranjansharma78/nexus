import pytest

from app.brain.ontology.transitions import (
    TERMINAL_TRANSITIONS,
    UniversalTransition,
    is_terminal_transition,
)


def test_transition_values_are_stable():
    assert UniversalTransition.OBSERVED.value == "observed"
    assert UniversalTransition.TRANSFERRED.value == "transferred"
    assert UniversalTransition.CLOSED.value == "closed"


@pytest.mark.parametrize(
    "transition",
    [
        UniversalTransition.SETTLED,
        UniversalTransition.REJECTED,
        UniversalTransition.FAILED,
        UniversalTransition.CANCELLED,
        UniversalTransition.EXPIRED,
        UniversalTransition.CLOSED,
    ],
)
def test_terminal_transitions_are_detected(transition):
    assert transition in TERMINAL_TRANSITIONS
    assert is_terminal_transition(transition) is True


@pytest.mark.parametrize(
    "transition",
    [
        UniversalTransition.OBSERVED,
        UniversalTransition.REQUESTED,
        UniversalTransition.COMMITTED,
        UniversalTransition.STARTED,
        UniversalTransition.PROGRESSED,
        UniversalTransition.TRANSFERRED,
        UniversalTransition.RECEIVED,
    ],
)
def test_non_terminal_transitions_remain_open(transition):
    assert is_terminal_transition(transition) is False


def test_string_input_is_supported():
    assert is_terminal_transition("closed") is True
    assert is_terminal_transition("started") is False


def test_invalid_transition_raises_value_error():
    with pytest.raises(ValueError):
        is_terminal_transition("not-a-transition")
