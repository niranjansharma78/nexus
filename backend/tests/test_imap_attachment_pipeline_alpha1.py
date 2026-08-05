from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.connectors.imap_sensor import EmailAttachment
from app.core.database import get_connection
from app.core.migrations import run_migrations
from app.services.imap_intelligence_service import process_email_intelligence


def test_email_attachment_creates_business_events(tmp_path, monkeypatch):
    run_migrations()

    import app.services.imap_intelligence_service as service

    monkeypatch.setattr(service, "ATTACHMENT_ROOT", tmp_path)

    mailbox_username = f"test-{uuid4().hex}@example.com"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO mailbox_profiles(
                label,host,port,username,folder,use_ssl
            )
            VALUES('Test','imap.test',993,?,'INBOX',1)
            """,
            (mailbox_username,),
        )
        profile_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

        conn.execute(
            """
            INSERT INTO evidence(
                source,evidence_type,title,summary,domain,
                occurred_at,confidence,status,requires_decision,priority
            )
            VALUES(
                'IMAP','communication','PO Attached',
                'Please find attached purchase order.',
                'business','2026-08-04T10:00:00+00:00',
                .9,'recorded',0,2
            )
            """
        )
        evidence_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

    attachment_text = (
        "Purchase Order\n"
        "Buyer: Excell Telesonic Private Limited\n"
        "PO No: ETPL/PO/4587\n"
        "Total Quantity: 128.4 km\n"
        "Grand Total: INR 46,80,000\n"
    ).encode("utf-8")

    item = SimpleNamespace(
        title="PO Attached",
        summary="Please find attached purchase order.",
        entity_name="Excell Telesonic",
        occurred_at="2026-08-04T10:00:00+00:00",
        attachments=[
            EmailAttachment(
                filename="purchase_order.txt",
                content_type="text/plain",
                payload=attachment_text,
            )
        ],
    )

    result = process_email_intelligence(
        evidence_id=evidence_id,
        profile_id=profile_id,
        mailbox_username=mailbox_username,
        fingerprint="a" * 64,
        item=item,
    )

    assert len(result["attachments"]) == 1
    assert any(
        event["event_type"] == "purchase_order_received"
        for event in result["attachment_events"]
    )

    with get_connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM business_events
            WHERE evidence_id=?
              AND event_type='purchase_order_received'
            """,
            (evidence_id,),
        ).fetchone()["count"]

    assert count >= 1
