from app.core.database import get_connection
from app.core.migrations import run_migrations
from app.services.conversation_engine_service import correlate_event


def test_dispatch_creates_open_delivery_conversation():
    run_migrations()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO business_events(
                event_type,visibility,summary,entity_name,
                reference_number,occurred_at,confidence
            )
            VALUES(
                'dispatch_details_received',
                'notice',
                'Dispatch details received',
                'Excell Telesonic',
                'LR45879652',
                '2026-08-04T10:00:00+00:00',
                .9
            )
            """
        )
        event_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

        event = dict(
            conn.execute(
                "SELECT * FROM business_events WHERE id=?",
                (event_id,),
            ).fetchone()
        )

    conversation = correlate_event(event)

    assert conversation["intent"] == "fulfilment"
    assert conversation["current_stage"] == "dispatched"
    assert conversation["expected_next_event"] == "delivery_confirmation"
    assert conversation["status"] == "open"
