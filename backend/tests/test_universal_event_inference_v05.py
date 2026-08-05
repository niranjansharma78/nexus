import pytest

from app.brain.ontology.domain_pack import DomainMapping, DomainPack
from app.brain.ontology.registry import DomainPackRegistry
from app.brain.ontology.transitions import UniversalTransition
from app.brain.reasoning.event_inference import (
    EventInferenceInput,
    infer_universal_event,
)


def test_unknown_input_defaults_to_observed_event():
    result = infer_universal_event(
        EventInferenceInput(
            title="Unfamiliar communication",
            summary="No known vocabulary is present",
            source="email",
            confidence=0.62,
        )
    )

    assert result.matched is False
    assert result.event.transition == UniversalTransition.OBSERVED
    assert result.event.intent == "observation"
    assert result.event.object.kind == "event"
    assert result.event.confidence == 0.62


def test_dispatch_deployment_and_shipment_use_same_transition():
    samples = [
        "Goods dispatched to the customer",
        "Software release deployed to production",
        "Retail order shipped to the buyer",
    ]

    transitions = {
        infer_universal_event(
            EventInferenceInput(
                title=sample,
                summary="",
                source="email",
            )
        ).event.transition
        for sample in samples
    }

    assert transitions == {UniversalTransition.TRANSFERRED}


def test_inference_preserves_actor_counterparty_and_value():
    result = infer_universal_event(
        EventInferenceInput(
            title="Payment received",
            summary="Customer payment credited",
            source="bank_email",
            actor_label="Customer A",
            counterparty_label="Company B",
            amount=250000.0,
            currency="INR",
            importance=95,
            evidence_id=42,
        )
    )

    event = result.event

    assert event.actor is not None
    assert event.actor.label == "Customer A"
    assert event.counterparty is not None
    assert event.counterparty.label == "Company B"
    assert event.value.amount == 250000.0
    assert event.value.currency == "INR"
    assert event.evidence_id == 42
    assert event.transition == UniversalTransition.SETTLED
    assert event.is_closed is True


def test_named_pack_limit_is_respected():
    registry = DomainPackRegistry()
    registry.register(
        DomainPack(
            name="alpha",
            version="1.0",
            mappings=[
                DomainMapping(
                    term="alpha signal",
                    object_kind="event",
                    transition=UniversalTransition.STARTED,
                    intent="alpha",
                )
            ],
        )
    )
    registry.register(
        DomainPack(
            name="beta",
            version="1.0",
            mappings=[
                DomainMapping(
                    term="beta signal",
                    object_kind="event",
                    transition=UniversalTransition.COMPLETED,
                    intent="beta",
                )
            ],
        )
    )

    result = infer_universal_event(
        EventInferenceInput(
            title="beta signal",
            summary="",
            source="test",
            pack_names=("alpha",),
        ),
        registry=registry,
    )

    assert result.matched is False
    assert result.event.transition == UniversalTransition.OBSERVED


def test_longest_matching_phrase_is_used_during_inference():
    registry = DomainPackRegistry()
    registry.register(
        DomainPack(
            name="settlement",
            version="1.0",
            mappings=[
                DomainMapping(
                    term="payment",
                    object_kind="transaction",
                    transition=UniversalTransition.REQUESTED,
                    intent="settlement_request",
                ),
                DomainMapping(
                    term="payment received",
                    object_kind="transaction",
                    transition=UniversalTransition.SETTLED,
                    intent="settlement",
                ),
            ],
        )
    )

    result = infer_universal_event(
        EventInferenceInput(
            title="Payment received from customer",
            summary="",
            source="test",
        ),
        registry=registry,
    )

    assert result.matched is True
    assert result.matched_term == "payment received"
    assert result.event.transition == UniversalTransition.SETTLED


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        EventInferenceInput(
            title="",
            summary="",
            source="email",
        )

    with pytest.raises(ValueError):
        EventInferenceInput(
            title="Something happened",
            summary="",
            source="email",
            confidence=1.5,
        )
