from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from app.core.database import get_connection
from app.core.migrations import run_migrations


INTENT_MAP = {
    "purchase_order_received": ("commercial_commitment", "received", "production_confirmation"),
    "production_confirmed": ("fulfilment", "confirmed", "dispatch"),
    "dispatch_details_received": ("fulfilment", "dispatched", "delivery_confirmation"),
    "delivery_confirmation_expected": ("fulfilment", "awaiting_delivery", "delivery_confirmation"),
    "payment_received": ("settlement", "received", None),
    "cheque_bounce": ("settlement", "failed", "payment_resolution"),
    "payment_failure": ("settlement", "failed", "payment_resolution"),
    "customer_complaint": ("issue", "raised", "resolution_confirmation"),
    "planning_delegation_suggested": ("delegation", "suggested", "owner_acknowledgement"),
}


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _conversation_key(event: dict[str, Any]) -> str:
    reference = _normalize(event.get("reference_number"))
    entity = _normalize(event.get("entity_name"))
    event_type = event.get("event_type") or "unknown"

    if reference:
        basis = f"ref:{reference}"
    elif entity:
        family = INTENT_MAP.get(event_type, (event_type, "", ""))[0]
        basis = f"entity:{entity}|family:{family}"
    else:
        basis = f"evidence:{event.get('evidence_id')}|type:{event_type}"

    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _health_for(stage: str, visibility: str) -> str:
    if visibility == "alert":
        return "critical"
    if stage in {"failed", "awaiting_delivery"}:
        return "watch"
    return "healthy"


def correlate_event(event: dict[str, Any]) -> dict[str, Any]:
    run_migrations()

    event_type = event["event_type"]
    intent, stage, expected_next = INTENT_MAP.get(
        event_type,
        ("general", "observed", None),
    )

    key = _conversation_key(event)
    now = datetime.now(timezone.utc).isoformat()
    subject = (
        event.get("summary")
        or event.get("entity_name")
        or event_type.replace("_", " ").title()
    )
    health = _health_for(stage, event.get("visibility", ""))

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT *
            FROM conversations
            WHERE conversation_key=?
            """,
            (key,),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE conversations
                SET current_stage=?,
                    expected_next_event=?,
                    status=?,
                    health=?,
                    updated_at=?,
                    confidence=MAX(confidence,?)
                WHERE id=?
                """,
                (
                    stage,
                    expected_next,
                    "closed" if expected_next is None else "open",
                    health,
                    now,
                    float(event.get("confidence") or 0.5),
                    existing["id"],
                ),
            )
            conversation_id = int(existing["id"])
        else:
            conn.execute(
                """
                INSERT INTO conversations(
                    conversation_key,
                    role_blueprint,
                    intent,
                    subject,
                    current_stage,
                    expected_closure,
                    expected_next_event,
                    status,
                    health,
                    opened_at,
                    updated_at,
                    confidence
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    key,
                    "universal",
                    intent,
                    subject,
                    stage,
                    expected_next,
                    expected_next,
                    "closed" if expected_next is None else "open",
                    health,
                    now,
                    now,
                    float(event.get("confidence") or 0.5),
                ),
            )
            conversation_id = int(
                conn.execute(
                    "SELECT last_insert_rowid() AS id"
                ).fetchone()["id"]
            )

        business_event_id = event.get("id")
        if business_event_id:
            next_sequence = conn.execute(
                """
                SELECT COALESCE(MAX(sequence_no),0)+1 AS seq
                FROM conversation_events
                WHERE conversation_id=?
                """,
                (conversation_id,),
            ).fetchone()["seq"]

            conn.execute(
                """
                INSERT OR IGNORE INTO conversation_events(
                    conversation_id,
                    business_event_id,
                    sequence_no
                )
                VALUES(?,?,?)
                """,
                (
                    conversation_id,
                    business_event_id,
                    next_sequence,
                ),
            )

        row = conn.execute(
            "SELECT * FROM conversations WHERE id=?",
            (conversation_id,),
        ).fetchone()

    return dict(row)


def correlate_unlinked_events(limit: int = 500) -> dict[str, int]:
    run_migrations()

    with get_connection() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT be.*
                FROM business_events be
                LEFT JOIN conversation_events ce
                  ON ce.business_event_id=be.id
                WHERE ce.business_event_id IS NULL
                ORDER BY be.id
                LIMIT ?
                """,
                (max(1, min(limit, 5000)),),
            ).fetchall()
        ]

    linked = 0
    for row in rows:
        correlate_event(row)
        linked += 1

    return {"reviewed": len(rows), "linked": linked}


def list_conversations(
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    run_migrations()

    where = ""
    params: list[Any] = []

    if status:
        where = "WHERE c.status=?"
        params.append(status)

    params.append(max(1, min(limit, 500)))

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                c.*,
                COUNT(ce.business_event_id) AS event_count
            FROM conversations c
            LEFT JOIN conversation_events ce
              ON ce.conversation_id=c.id
            {where}
            GROUP BY c.id
            ORDER BY
                CASE c.health
                  WHEN 'critical' THEN 0
                  WHEN 'watch' THEN 1
                  ELSE 2
                END,
                c.updated_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

    return [dict(row) for row in rows]
