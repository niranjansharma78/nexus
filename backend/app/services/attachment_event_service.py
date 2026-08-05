from __future__ import annotations

from app.services.attachment_intelligence_service import AttachmentExtraction


def events_from_attachment(
    extraction: AttachmentExtraction,
) -> list[dict]:
    data = extraction.structured_data
    events: list[dict] = []

    common = {
        "entity_name": data.get("customer"),
        "quantity": data.get("quantity_km"),
        "unit": "km" if data.get("quantity_km") is not None else None,
        "value_amount": data.get("value_amount"),
        "currency": data.get("currency"),
        "confidence": extraction.confidence,
        "review_required": extraction.review_required,
    }

    if extraction.document_type == "purchase_order":
        events.append({
            "event_type": "purchase_order_received",
            "visibility": "notice",
            "summary": (
                "Purchase order received"
                + (
                    f" from {data['customer']}"
                    if data.get("customer")
                    else ""
                )
            ),
            "reference_number": data.get("po_number"),
            **common,
        })

    if extraction.document_type == "dispatch":
        events.append({
            "event_type": "dispatch_details_received",
            "visibility": "notice",
            "summary": (
                "Dispatch details received"
                + (
                    f" for {data['customer']}"
                    if data.get("customer")
                    else ""
                )
            ),
            "reference_number": (
                data.get("invoice_number")
                or data.get("lr_number")
            ),
            **common,
        })

        events.append({
            "event_type": "delivery_confirmation_expected",
            "visibility": "monitor",
            "summary": "Monitor communication until delivery confirmation.",
            "reference_number": data.get("lr_number"),
            **common,
        })

    return events
