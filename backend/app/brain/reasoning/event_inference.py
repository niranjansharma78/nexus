from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.brain.ontology.models import (
    UniversalEvent,
    UniversalObjectRef,
    ValueMeasure,
)
from app.brain.ontology.registry import (
    DEFAULT_DOMAIN_PACK_REGISTRY,
    DomainPackRegistry,
)
from app.brain.ontology.transitions import UniversalTransition


@dataclass(slots=True, frozen=True)
class EventInferenceInput:
    title: str
    summary: str
    source: str
    world: str = "business"
    actor_label: str | None = None
    actor_kind: str = "person_or_organization"
    counterparty_label: str | None = None
    counterparty_kind: str = "person_or_organization"
    evidence_id: int | None = None
    confidence: float = 0.50
    amount: float | None = None
    currency: str | None = None
    quantity: float | None = None
    unit: str | None = None
    importance: int | None = None
    organization_id: str | None = None
    pack_names: tuple[str, ...] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.title.strip() and not self.summary.strip():
            raise ValueError("Title or summary is required")
        if not self.source.strip():
            raise ValueError("Source is required")
        if not self.world.strip():
            raise ValueError("World is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")


@dataclass(slots=True, frozen=True)
class EventInferenceResult:
    event: UniversalEvent
    matched_pack: str | None
    matched_term: str | None
    matched: bool


def _build_party(
    label: str | None,
    kind: str,
) -> UniversalObjectRef | None:
    if label is None or not label.strip():
        return None
    return UniversalObjectRef(kind=kind, label=label.strip())


def infer_universal_event(
    payload: EventInferenceInput,
    *,
    registry: DomainPackRegistry | None = None,
) -> EventInferenceResult:
    active_registry = registry or DEFAULT_DOMAIN_PACK_REGISTRY
    combined_text = "\n".join(
        part for part in (payload.title.strip(), payload.summary.strip()) if part
    )

    resolved = active_registry.resolve(
        combined_text,
        pack_names=list(payload.pack_names) if payload.pack_names else None,
    )

    if resolved is None:
        matched_pack = None
        matched_term = None
        matched = False
        object_kind = "event"
        intent = "observation"
        transition = UniversalTransition.OBSERVED
        expected_next = None
    else:
        pack, mapping = resolved
        matched_pack = pack.name
        matched_term = mapping.term
        matched = True
        object_kind = mapping.object_kind
        intent = mapping.intent
        transition = mapping.transition
        expected_next = mapping.expected_next

    label = payload.title.strip() or payload.summary.strip()

    event = UniversalEvent(
        object=UniversalObjectRef(
            kind=object_kind,
            label=label,
        ),
        intent=intent,
        transition=transition,
        state=transition.value,
        world=payload.world.strip(),
        confidence=float(payload.confidence),
        source=payload.source.strip(),
        actor=_build_party(payload.actor_label, payload.actor_kind),
        counterparty=_build_party(
            payload.counterparty_label,
            payload.counterparty_kind,
        ),
        value=ValueMeasure(
            amount=payload.amount,
            currency=payload.currency,
            quantity=payload.quantity,
            unit=payload.unit,
            importance=payload.importance,
        ),
        evidence_id=payload.evidence_id,
        expected_next=expected_next,
        organization_id=payload.organization_id,
        domain_pack=matched_pack,
        metadata={
            **payload.metadata,
            "input_title": payload.title,
            "input_summary": payload.summary,
            "matched_term": matched_term,
        },
    )

    return EventInferenceResult(
        event=event,
        matched_pack=matched_pack,
        matched_term=matched_term,
        matched=matched,
    )
