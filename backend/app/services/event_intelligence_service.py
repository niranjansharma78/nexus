from __future__ import annotations

import re
from dataclasses import dataclass, asdict


@dataclass(slots=True)
class ExtractedEvent:
    event_type: str
    visibility: str
    summary: str
    entity_name: str | None = None
    reference_number: str | None = None
    quantity: float | None = None
    unit: str | None = None
    value_amount: float | None = None
    currency: str | None = None
    confidence: float = 0.7

    def to_dict(self) -> dict:
        return asdict(self)


CRITICAL_PATTERNS = {
    "cheque_bounce": (
        r"cheque\s+(?:bounce|bounced|returned)",
        r"payment\s+dishonou?red",
        r"instrument\s+returned",
    ),
    "payment_failure": (
        r"payment\s+(?:failed|declined|rejected)",
        r"transaction\s+(?:failed|declined)",
    ),
    "customer_complaint": (
        r"\bcomplaint\b",
        r"not\s+satisfied",
        r"quality\s+issue",
    ),
}

NOTICE_PATTERNS = {
    "purchase_order_received": (
        r"purchase\s+order",
        r"\bpo\s+(?:received|attached|enclosed|issued)",
    ),
    "production_confirmed": (
        r"production\s+(?:confirmation|confirmed|completed)",
    ),
    "dispatch_details_received": (
        r"dispatch\s+details",
        r"despatch\s+details",
        r"\bdispatched\b",
        r"\bdespatched\b",
    ),
    "payment_received": (
        r"\bcredited\b",
        r"payment\s+received",
    ),
}

PO_NUMBER_RE = re.compile(
    r"\b(?:po|purchase\s+order)\s*(?:no\.?|number|#|:)?\s*([A-Z0-9/_-]{4,})",
    re.IGNORECASE,
)

VALUE_RE = re.compile(
    r"(?:₹|inr|rs\.?)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)

KM_RE = re.compile(
    r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:km|kms|kilometres|kilometers)\b",
    re.IGNORECASE,
)


def _first_match(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _amount(text: str) -> float | None:
    match = VALUE_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _km(text: str) -> float | None:
    match = KM_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_business_events(
    *,
    title: str,
    summary: str,
    entity_name: str | None = None,
) -> list[dict]:
    text = f"{title or ''} {summary or ''}".strip()
    events: list[ExtractedEvent] = []

    for event_type, patterns in CRITICAL_PATTERNS.items():
        if _first_match(text, patterns):
            label = event_type.replace("_", " ").title()
            events.append(
                ExtractedEvent(
                    event_type=event_type,
                    visibility="alert",
                    summary=label,
                    entity_name=entity_name,
                    value_amount=_amount(text),
                    currency="INR" if _amount(text) is not None else None,
                    confidence=0.92,
                )
            )

    for event_type, patterns in NOTICE_PATTERNS.items():
        if not _first_match(text, patterns):
            continue

        label = event_type.replace("_", " ").title()
        po_match = PO_NUMBER_RE.search(text)

        events.append(
            ExtractedEvent(
                event_type=event_type,
                visibility="notice",
                summary=label,
                entity_name=entity_name,
                reference_number=po_match.group(1) if po_match else None,
                quantity=_km(text),
                unit="km" if _km(text) is not None else None,
                value_amount=_amount(text),
                currency="INR" if _amount(text) is not None else None,
                confidence=0.84,
            )
        )

    # Production confirmation should naturally suggest Planning.
    if any(event.event_type == "production_confirmed" for event in events):
        events.append(
            ExtractedEvent(
                event_type="planning_delegation_suggested",
                visibility="delegate",
                summary="Planning should review production and dispatch requirements.",
                entity_name="Planning",
                confidence=0.82,
            )
        )

    # Dispatch creates a communication-closure watch, not an ERP workflow.
    if any(event.event_type == "dispatch_details_received" for event in events):
        events.append(
            ExtractedEvent(
                event_type="delivery_confirmation_expected",
                visibility="monitor",
                summary="Monitor communication until delivery confirmation is received.",
                entity_name=entity_name,
                confidence=0.8,
            )
        )

    return [event.to_dict() for event in events]
