from __future__ import annotations

from datetime import datetime, timezone

from app.core.database import get_connection
from app.core.migrations import run_migrations


ALLOWED_FEEDBACK = {
    "always_alert",
    "always_show",
    "delegate_to",
    "suppress",
    "wrong_category",
    "wrong_company",
    "wrong_amount",
    "wrong_source",
    "internal_transfer",
    "not_relevant",
    "lock_rule",
    "unlock_rule",
}


def record_feedback(
    *,
    feedback_type: str,
    evidence_id: int | None = None,
    business_event_id: int | None = None,
    original_value: str | None = None,
    corrected_value: str | None = None,
    note: str | None = None,
) -> dict:
    run_migrations()

    if feedback_type not in ALLOWED_FEEDBACK:
        raise ValueError(f"Unsupported feedback type: {feedback_type}")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_feedback(
                evidence_id,
                business_event_id,
                feedback_type,
                original_value,
                corrected_value,
                note,
                created_at
            )
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                evidence_id,
                business_event_id,
                feedback_type,
                original_value,
                corrected_value,
                note,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        feedback_id = int(
            conn.execute(
                "SELECT last_insert_rowid() AS id"
            ).fetchone()["id"]
        )

        if business_event_id and feedback_type == "always_alert":
            conn.execute(
                """
                UPDATE business_events
                SET visibility='alert',
                    confidence=1.0
                WHERE id=?
                """,
                (business_event_id,),
            )

        if business_event_id and feedback_type == "always_show":
            conn.execute(
                """
                UPDATE business_events
                SET visibility='notice',
                    confidence=1.0
                WHERE id=?
                """,
                (business_event_id,),
            )

        if business_event_id and feedback_type == "suppress":
            conn.execute(
                """
                UPDATE business_events
                SET visibility='quiet',
                    confidence=1.0
                WHERE id=?
                """,
                (business_event_id,),
            )

    return {
        "id": feedback_id,
        "feedback_type": feedback_type,
        "applied": True,
    }


def feedback_summary() -> dict:
    run_migrations()

    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS count FROM user_feedback"
        ).fetchone()["count"]

        by_type = {
            row["feedback_type"]: row["count"]
            for row in conn.execute(
                """
                SELECT feedback_type,COUNT(*) AS count
                FROM user_feedback
                GROUP BY feedback_type
                ORDER BY count DESC
                """
            ).fetchall()
        }

    return {
        "total": total,
        "by_type": by_type,
    }
