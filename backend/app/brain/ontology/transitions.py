from __future__ import annotations

from enum import StrEnum


class UniversalTransition(StrEnum):
    OBSERVED = "observed"
    REQUESTED = "requested"
    PROPOSED = "proposed"
    COMMITTED = "committed"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    STARTED = "started"
    PROGRESSED = "progressed"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    SETTLED = "settled"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ESCALATED = "escalated"
    CLOSED = "closed"


TERMINAL_TRANSITIONS: frozenset[UniversalTransition] = frozenset(
    {
        UniversalTransition.SETTLED,
        UniversalTransition.REJECTED,
        UniversalTransition.FAILED,
        UniversalTransition.CANCELLED,
        UniversalTransition.EXPIRED,
        UniversalTransition.CLOSED,
    }
)


def is_terminal_transition(
    transition: UniversalTransition | str,
) -> bool:
    return UniversalTransition(transition) in TERMINAL_TRANSITIONS
