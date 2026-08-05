from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.core.database import get_connection
from app.services.attachment_event_service import events_from_attachment
from app.services.attachment_intelligence_service import (
    SUPPORTED_EXTENSIONS,
    analyze_attachment,
)
from app.services.event_intelligence_service import extract_business_events


ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_ROOT = ROOT / "data" / "attachments"


def _safe_component(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned[:100] or "item"


def _store_event(
    conn,
    *,
    evidence_id: int,
    event: dict,
    occurred_at: str,
) -> int:
    structured = {
        key: value
        for key, value in event.items()
        if key not in {
            "event_type",
            "visibility",
            "summary",
            "entity_name",
            "reference_number",
            "quantity",
            "unit",
            "value_amount",
            "currency",
            "confidence",
        }
    }

    conn.execute(
        """
        INSERT INTO business_events(
            evidence_id,
            event_type,
            visibility,
            entity_name,
            reference_number,
            quantity,
            unit,
            value_amount,
            currency,
            occurred_at,
            confidence,
            summary,
            structured_data
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            evidence_id,
            event.get("event_type"),
            event.get("visibility"),
            event.get("entity_name"),
            event.get("reference_number"),
            event.get("quantity"),
            event.get("unit"),
            event.get("value_amount"),
            event.get("currency"),
            occurred_at,
            event.get("confidence", 0.5),
            event.get("summary") or event.get("event_type"),
            json.dumps(structured, ensure_ascii=False),
        ),
    )

    return int(
        conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]
    )


def process_email_intelligence(
    *,
    evidence_id: int,
    profile_id: int,
    mailbox_username: str,
    fingerprint: str,
    item,
) -> dict:
    body_events = extract_business_events(
        title=item.title,
        summary=item.summary,
        entity_name=item.entity_name,
    )

    attachment_results: list[dict] = []
    attachment_events: list[dict] = []

    message_dir = (
        ATTACHMENT_ROOT
        / _safe_component(mailbox_username)
        / fingerprint[:16]
    )
    message_dir.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        for event in body_events:
            _store_event(
                conn,
                evidence_id=evidence_id,
                event=event,
                occurred_at=item.occurred_at,
            )

        for attachment in item.attachments:
            filename = _safe_component(attachment.filename)
            path = message_dir / filename

            # Avoid overwriting attachments with the same name.
            suffix = 1
            while path.exists():
                path = message_dir / (
                    f"{Path(filename).stem}_{suffix}"
                    f"{Path(filename).suffix}"
                )
                suffix += 1

            path.write_bytes(attachment.payload)
            sha256 = hashlib.sha256(attachment.payload).hexdigest()
            extension = path.suffix.lower()

            extraction_status = "unsupported"
            extracted_text = None
            structured_data = None
            extraction_confidence = None

            if extension in SUPPORTED_EXTENSIONS:
                try:
                    extraction = analyze_attachment(path)
                    extraction_status = "completed"
                    extracted_text = extraction.text
                    structured_data = extraction.structured_data
                    extraction_confidence = extraction.confidence

                    events = events_from_attachment(extraction)
                    attachment_events.extend(events)

                    for event in events:
                        _store_event(
                            conn,
                            evidence_id=evidence_id,
                            event=event,
                            occurred_at=item.occurred_at,
                        )

                except Exception as exc:
                    extraction_status = "failed"
                    structured_data = {
                        "error": str(exc),
                    }

            conn.execute(
                """
                INSERT INTO attachments(
                    evidence_id,
                    mailbox_profile_id,
                    filename,
                    content_type,
                    size_bytes,
                    storage_path,
                    sha256,
                    extraction_status,
                    extracted_text,
                    structured_data,
                    extraction_confidence
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    evidence_id,
                    profile_id,
                    attachment.filename,
                    attachment.content_type,
                    len(attachment.payload),
                    str(path),
                    sha256,
                    extraction_status,
                    extracted_text,
                    json.dumps(
                        structured_data,
                        ensure_ascii=False,
                    )
                    if structured_data is not None
                    else None,
                    extraction_confidence,
                ),
            )

            attachment_results.append({
                "filename": attachment.filename,
                "status": extraction_status,
                "document_type": (
                    extraction.document_type
                    if extraction_status == "completed"
                    else None
                ),
                "structured_data": structured_data,
            })

    return {
        "body_events": body_events,
        "attachment_events": attachment_events,
        "attachments": attachment_results,
    }
