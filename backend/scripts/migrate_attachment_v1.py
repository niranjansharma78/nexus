from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import get_connection


with get_connection() as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )

    existing = conn.execute(
        "SELECT version FROM schema_migrations WHERE version=2"
    ).fetchone()

    if existing:
        print("Attachment migration already applied.")
    else:
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_attachments_status
            ON attachments(extraction_status);

            CREATE INDEX IF NOT EXISTS idx_attachments_sha256
            ON attachments(sha256);

            CREATE INDEX IF NOT EXISTS idx_business_events_reference
            ON business_events(reference_number);
            """
        )

        conn.execute(
            """
            INSERT INTO schema_migrations(version,name,applied_at)
            VALUES(2,'attachment_intelligence_v1',CURRENT_TIMESTAMP)
            """
        )
        print("Attachment migration applied.")
