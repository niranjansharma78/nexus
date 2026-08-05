from __future__ import annotations

from app.core.database import get_connection


def ensure_delegation_schema() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS nexus_delegations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id INTEGER,
                title TEXT NOT NULL,
                summary TEXT,
                owner TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(evidence_id, owner, status)
            );

            CREATE INDEX IF NOT EXISTS idx_nexus_delegations_status
            ON nexus_delegations(status);

            CREATE TABLE IF NOT EXISTS nexus_monitor_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'watching',
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def create_delegation(
    *,
    evidence_id: int | None,
    title: str,
    summary: str | None,
    owner: str,
    note: str | None = None,
) -> dict:
    ensure_delegation_schema()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO nexus_delegations(
                evidence_id,title,summary,owner,status,note
            )
            VALUES(?,?,?,?, 'open', ?)
            """,
            (evidence_id, title, summary, owner, note),
        )
        row = conn.execute(
            """
            SELECT *
            FROM nexus_delegations
            WHERE evidence_id IS ?
              AND owner=?
              AND status='open'
            ORDER BY id DESC
            LIMIT 1
            """,
            (evidence_id, owner),
        ).fetchone()
    return dict(row) if row else {"ok": True}


def update_delegation_status(delegation_id: int, status: str, note: str | None = None) -> dict:
    ensure_delegation_schema()
    allowed = {"open", "in_progress", "done", "cancelled"}
    if status not in allowed:
        raise ValueError("Invalid delegation status")

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE nexus_delegations
            SET status=?,
                note=COALESCE(?,note),
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (status, note, delegation_id),
        )
        row = conn.execute(
            "SELECT * FROM nexus_delegations WHERE id=?",
            (delegation_id,),
        ).fetchone()

    if not row:
        raise ValueError("Delegation not found")
    return dict(row)


def list_delegations(status: str | None = None) -> list[dict]:
    ensure_delegation_schema()
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT *
                FROM nexus_delegations
                WHERE status=?
                ORDER BY id DESC
                """,
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM nexus_delegations
                ORDER BY
                    CASE status
                        WHEN 'open' THEN 1
                        WHEN 'in_progress' THEN 2
                        WHEN 'done' THEN 3
                        ELSE 4
                    END,
                    id DESC
                """
            ).fetchall()
    return [dict(row) for row in rows]


def set_monitor_status(evidence_id: int, status: str, note: str | None = None) -> dict:
    ensure_delegation_schema()
    allowed = {"watching", "acknowledged", "closed"}
    if status not in allowed:
        raise ValueError("Invalid monitor status")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO nexus_monitor_actions(evidence_id,status,note)
            VALUES(?,?,?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                status=excluded.status,
                note=COALESCE(excluded.note,nexus_monitor_actions.note),
                updated_at=CURRENT_TIMESTAMP
            """,
            (evidence_id, status, note),
        )
        row = conn.execute(
            "SELECT * FROM nexus_monitor_actions WHERE evidence_id=?",
            (evidence_id,),
        ).fetchone()
    return dict(row)
