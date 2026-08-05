from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.core.database import get_connection
from app.core.migrations import run_migrations


ORDER = {
    "alert": 0,
    "notice": 1,
    "delegate": 2,
    "monitor": 3,
}


def executive_feed(
    *,
    hours: int = 168,
    limit_per_section: int = 10,
) -> dict:
    run_migrations()

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=max(1, min(hours, 2160)))
    ).isoformat()

    with get_connection() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT
                    be.id,
                    be.evidence_id,
                    be.event_type,
                    be.visibility,
                    be.entity_name,
                    be.reference_number,
                    be.quantity,
                    be.unit,
                    be.value_amount,
                    be.currency,
                    be.occurred_at,
                    be.confidence,
                    be.summary,
                    be.structured_data,
                    e.title AS evidence_title,
                    e.source
                FROM business_events be
                LEFT JOIN evidence e
                  ON e.id=be.evidence_id
                WHERE COALESCE(be.occurred_at,be.created_at) >= ?
                ORDER BY
                    CASE be.visibility
                      WHEN 'alert' THEN 0
                      WHEN 'notice' THEN 1
                      WHEN 'delegate' THEN 2
                      WHEN 'monitor' THEN 3
                      ELSE 4
                    END,
                    be.id DESC
                """,
                (since,),
            ).fetchall()
        ]

    sections = {
        "alerts": [],
        "notices": [],
        "delegations": [],
        "monitoring": [],
    }

    section_for = {
        "alert": "alerts",
        "notice": "notices",
        "delegate": "delegations",
        "monitor": "monitoring",
    }

    seen: set[tuple] = set()

    for row in rows:
        section = section_for.get(row["visibility"])
        if not section:
            continue

        key = (
            row["event_type"],
            row["evidence_id"],
            row["reference_number"],
            row["quantity"],
            row["value_amount"],
        )
        if key in seen:
            continue
        seen.add(key)

        try:
            structured = json.loads(
                row.get("structured_data") or "{}"
            )
        except json.JSONDecodeError:
            structured = {}

        item = {
            "id": row["id"],
            "evidence_id": row["evidence_id"],
            "type": row["event_type"],
            "summary": row["summary"],
            "entity": row["entity_name"],
            "reference": row["reference_number"],
            "quantity": row["quantity"],
            "unit": row["unit"],
            "value": row["value_amount"],
            "currency": row["currency"],
            "occurred_at": row["occurred_at"],
            "confidence": row["confidence"],
            "evidence_title": row["evidence_title"],
            "review_required": structured.get(
                "review_required",
                False,
            ),
        }

        if len(sections[section]) < limit_per_section:
            sections[section].append(item)

    return {
        "summary": {
            "alerts": len(sections["alerts"]),
            "notices": len(sections["notices"]),
            "delegations": len(sections["delegations"]),
            "monitoring": len(sections["monitoring"]),
        },
        **sections,
    }
