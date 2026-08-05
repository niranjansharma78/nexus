from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.core.database import get_connection


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable


def _migration_1(conn) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS business_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER,
            event_type TEXT NOT NULL,
            visibility TEXT NOT NULL,
            company_space_id INTEGER,
            entity_name TEXT,
            reference_number TEXT,
            quantity REAL,
            unit TEXT,
            value_amount REAL,
            currency TEXT,
            occurred_at TEXT,
            confidence REAL NOT NULL DEFAULT 0.5,
            summary TEXT NOT NULL,
            structured_data TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(evidence_id) REFERENCES evidence(id),
            FOREIGN KEY(company_space_id) REFERENCES nexus_spaces(id)
        );

        CREATE INDEX IF NOT EXISTS idx_business_events_evidence
        ON business_events(evidence_id);

        CREATE INDEX IF NOT EXISTS idx_business_events_visibility
        ON business_events(visibility);

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_key TEXT NOT NULL UNIQUE,
            role_blueprint TEXT NOT NULL,
            intent TEXT NOT NULL,
            company_space_id INTEGER,
            subject TEXT NOT NULL,
            current_stage TEXT NOT NULL,
            expected_closure TEXT,
            expected_next_event TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            health TEXT NOT NULL DEFAULT 'healthy',
            opened_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT,
            confidence REAL NOT NULL DEFAULT 0.5,
            FOREIGN KEY(company_space_id) REFERENCES nexus_spaces(id)
        );

        CREATE TABLE IF NOT EXISTS conversation_events (
            conversation_id INTEGER NOT NULL,
            business_event_id INTEGER NOT NULL,
            sequence_no INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(conversation_id, business_event_id),
            FOREIGN KEY(conversation_id) REFERENCES conversations(id),
            FOREIGN KEY(business_event_id) REFERENCES business_events(id)
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER,
            mailbox_profile_id INTEGER,
            filename TEXT NOT NULL,
            content_type TEXT,
            size_bytes INTEGER,
            storage_path TEXT,
            sha256 TEXT,
            extraction_status TEXT NOT NULL DEFAULT 'pending',
            extracted_text TEXT,
            structured_data TEXT,
            extraction_confidence REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(evidence_id) REFERENCES evidence(id),
            FOREIGN KEY(mailbox_profile_id) REFERENCES mailbox_profiles(id)
        );

        CREATE INDEX IF NOT EXISTS idx_attachments_evidence
        ON attachments(evidence_id);

        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id INTEGER,
            business_event_id INTEGER,
            feedback_type TEXT NOT NULL,
            original_value TEXT,
            corrected_value TEXT,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(evidence_id) REFERENCES evidence(id),
            FOREIGN KEY(business_event_id) REFERENCES business_events(id)
        );

        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_space_id INTEGER,
            bank_name TEXT NOT NULL,
            account_label TEXT NOT NULL,
            account_last4 TEXT,
            sender_patterns TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company_space_id, bank_name, account_label),
            FOREIGN KEY(company_space_id) REFERENCES nexus_spaces(id)
        );
        """
    )


MIGRATIONS = [
    Migration(1, "jarvis_intelligence_foundation", _migration_1),
]


def run_migrations() -> list[int]:
    applied: list[int] = []

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

        existing = {
            row["version"]
            for row in conn.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }

        for migration in MIGRATIONS:
            if migration.version in existing:
                continue

            migration.apply(conn)
            conn.execute(
                """
                INSERT INTO schema_migrations(version, name, applied_at)
                VALUES(?,?,?)
                """,
                (
                    migration.version,
                    migration.name,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            applied.append(migration.version)

    return applied
