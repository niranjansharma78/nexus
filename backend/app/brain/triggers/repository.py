from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import TriggerEnvelope, TriggerKind


class TriggerRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS runtime_triggers (
                    trigger_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    world TEXT,
                    source TEXT,
                    objective TEXT,
                    created_at TEXT NOT NULL,
                    fingerprint TEXT UNIQUE,
                    metadata_json TEXT NOT NULL,
                    processed INTEGER NOT NULL DEFAULT 0,
                    runtime_run_id TEXT,
                    error_text TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_runtime_triggers_processed
                    ON runtime_triggers(processed);

                CREATE INDEX IF NOT EXISTS idx_runtime_triggers_kind
                    ON runtime_triggers(kind);
                '''
            )

    def insert_if_new(self, trigger: TriggerEnvelope) -> bool:
        self.ensure_schema()
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT OR IGNORE INTO runtime_triggers (
                    trigger_id,
                    kind,
                    payload_json,
                    world,
                    source,
                    objective,
                    created_at,
                    fingerprint,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    trigger.trigger_id,
                    trigger.kind.value,
                    json.dumps(trigger.payload),
                    trigger.world,
                    trigger.source,
                    trigger.objective,
                    trigger.created_at,
                    trigger.fingerprint,
                    json.dumps(trigger.metadata),
                ),
            )
        return cursor.rowcount > 0

    def mark_processed(
        self,
        trigger_id: str,
        *,
        runtime_run_id: str | None = None,
        error_text: str | None = None,
    ) -> None:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                UPDATE runtime_triggers
                SET processed=1, runtime_run_id=?, error_text=?
                WHERE trigger_id=?
                ''',
                (runtime_run_id, error_text, trigger_id),
            )

    def list_pending(self, *, limit: int = 100) -> list[TriggerEnvelope]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM runtime_triggers
                WHERE processed=0
                ORDER BY created_at ASC
                LIMIT ?
                ''',
                (max(1, min(int(limit), 500)),),
            ).fetchall()

        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> TriggerEnvelope:
        return TriggerEnvelope(
            trigger_id=row["trigger_id"],
            kind=TriggerKind(row["kind"]),
            payload=json.loads(row["payload_json"]),
            world=row["world"],
            source=row["source"],
            objective=row["objective"],
            created_at=row["created_at"],
            fingerprint=row["fingerprint"],
            metadata=json.loads(row["metadata_json"]),
        )
