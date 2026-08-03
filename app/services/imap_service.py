from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import asdict

from app.connectors.imap_sensor import IMAPSensor, IMAPSettings
from app.core.database import get_connection


def ensure_tables() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mailbox_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT NOT NULL,
                folder TEXT NOT NULL DEFAULT 'INBOX',
                use_ssl INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_scan_at TEXT,
                last_scan_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(host, username, folder)
            );

            CREATE TABLE IF NOT EXISTS imap_message_index (
                fingerprint TEXT PRIMARY KEY,
                message_id TEXT,
                mailbox_username TEXT NOT NULL,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def save_profile(*, label: str, host: str, port: int, username: str, folder: str, use_ssl: bool) -> int:
    ensure_tables()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO mailbox_profiles(label,host,port,username,folder,use_ssl)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(host,username,folder) DO UPDATE SET
              label=excluded.label,
              port=excluded.port,
              use_ssl=excluded.use_ssl
            """,
            (label, host, port, username, folder, int(use_ssl)),
        )
        row = conn.execute(
            "SELECT id FROM mailbox_profiles WHERE host=? AND username=? AND folder=?",
            (host, username, folder),
        ).fetchone()
        return int(row["id"])


def list_profiles() -> list[dict]:
    ensure_tables()
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM mailbox_profiles ORDER BY id DESC"
        ).fetchall()]


def scan_mailbox(
    *,
    label: str,
    host: str,
    port: int,
    username: str,
    password: str,
    folder: str,
    use_ssl: bool,
    limit: int,
) -> dict:
    ensure_tables()
    sensor = IMAPSensor(IMAPSettings(
        host=host.strip(),
        port=port,
        username=username.strip(),
        password=password,
        folder=folder.strip() or "INBOX",
        use_ssl=use_ssl,
    ))
    connection = sensor.test_connection()
    evidence_items = sensor.scan_recent(limit=limit)
    profile_id = save_profile(
        label=label.strip() or username.strip(),
        host=host.strip(),
        port=port,
        username=username.strip(),
        folder=folder.strip() or "INBOX",
        use_ssl=use_ssl,
    )

    inserted = 0
    duplicates = 0

    with get_connection() as conn:
        for item in evidence_items:
            raw_key = item.message_id or (
                f"{item.sender}|{item.title}|{item.occurred_at}|{item.summary[:100]}"
            )
            fingerprint = hashlib.sha256(raw_key.encode("utf-8", errors="ignore")).hexdigest()

            try:
                conn.execute(
                    """
                    INSERT INTO imap_message_index(fingerprint,message_id,mailbox_username)
                    VALUES(?,?,?)
                    """,
                    (fingerprint, item.message_id, username.strip()),
                )
            except sqlite3.IntegrityError:
                duplicates += 1
                continue

            conn.execute(
                """
                INSERT INTO evidence(
                    source,evidence_type,title,summary,domain,occurred_at,
                    confidence,status,entity_name,amount,currency,
                    requires_decision,priority
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    item.source,
                    "communication",
                    item.title,
                    item.summary,
                    item.domain,
                    item.occurred_at,
                    item.confidence,
                    item.status,
                    item.entity_name,
                    None,
                    None,
                    item.requires_decision,
                    item.priority,
                ),
            )
            inserted += 1

        conn.execute(
            """
            UPDATE mailbox_profiles
            SET last_scan_at=CURRENT_TIMESTAMP,last_scan_count=?
            WHERE id=?
            """,
            (len(evidence_items), profile_id),
        )

    return {
        "ok": True,
        "connection": connection,
        "scanned": len(evidence_items),
        "inserted": inserted,
        "duplicates": duplicates,
        "profile_id": profile_id,
    }
