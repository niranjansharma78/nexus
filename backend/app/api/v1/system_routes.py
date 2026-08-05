from fastapi import APIRouter

from app.core.database import get_connection


router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/health")
def health():
    with get_connection() as conn:
        evidence_count = conn.execute(
            "SELECT COUNT(*) AS count FROM evidence"
        ).fetchone()["count"]

        migrations = [
            dict(row)
            for row in conn.execute(
                """
                SELECT version,name,applied_at
                FROM schema_migrations
                ORDER BY version
                """
            ).fetchall()
        ]

    return {
        "ok": True,
        "version": "0.4.0-alpha1",
        "evidence_count": evidence_count,
        "migrations": migrations,
    }


@router.get("/capabilities")
def capabilities():
    return {
        "ingestion": ["imap"],
        "intelligence": [
            "email_normalization",
            "multi_event_extraction_v1",
            "alerts",
            "notices",
            "delegation_suggestions",
            "closure_watch_scaffolding",
            "automatic_imap_attachment_capture",
            "executive_event_feed",
            "conversation_correlation_v1",
            "intelligence_feedback_controls",
        ],
        "attachments": {
            "inventory_schema": True,
            "extraction": "v1",
        },
        "clients": {
            "html_admin": True,
            "flutter": "next",
        },
    }
