from app.core.database import get_connection
from app.core.migrations import run_migrations
from app.services.intelligence_feedback_service import record_feedback


def test_always_alert_updates_event():
    run_migrations()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO business_events(
                event_type,visibility,summary,confidence
            )
            VALUES('production_confirmed','notice','Production confirmed',.8)
            """
        )
        event_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

    result = record_feedback(
        feedback_type="always_alert",
        business_event_id=event_id,
        note="Test correction",
    )

    assert result["applied"] is True

    with get_connection() as conn:
        row = conn.execute(
            "SELECT visibility,confidence FROM business_events WHERE id=?",
            (event_id,),
        ).fetchone()

    assert row["visibility"] == "alert"
    assert row["confidence"] == 1.0
