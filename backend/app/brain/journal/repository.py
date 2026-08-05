from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import (
    BrainJournalEntry,
    BrainJournalLearning,
    BrainJournalMetric,
)


class BrainJournalRepository:
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
                CREATE TABLE IF NOT EXISTS brain_journal_entries (
                    journal_id TEXT PRIMARY KEY,
                    journal_date TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    learnings_json TEXT NOT NULL,
                    corrections_json TEXT NOT NULL,
                    open_questions_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_brain_journal_scope_date
                    ON brain_journal_entries(scope, journal_date);
                '''
            )

    def save(self, entry: BrainJournalEntry) -> BrainJournalEntry:
        self.ensure_schema()
        data = entry.to_dict()

        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO brain_journal_entries (
                    journal_id,
                    journal_date,
                    scope,
                    summary,
                    metrics_json,
                    learnings_json,
                    corrections_json,
                    open_questions_json,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scope, journal_date) DO UPDATE SET
                    journal_id = excluded.journal_id,
                    summary = excluded.summary,
                    metrics_json = excluded.metrics_json,
                    learnings_json = excluded.learnings_json,
                    corrections_json = excluded.corrections_json,
                    open_questions_json = excluded.open_questions_json,
                    metadata_json = excluded.metadata_json
                ''',
                (
                    entry.journal_id,
                    entry.journal_date,
                    entry.scope,
                    entry.summary,
                    json.dumps(data["metrics"]),
                    json.dumps(data["learnings"]),
                    json.dumps(entry.corrections),
                    json.dumps(entry.open_questions),
                    json.dumps(entry.metadata),
                ),
            )

        return entry

    def get(self, scope: str, journal_date: str) -> BrainJournalEntry | None:
        self.ensure_schema()

        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM brain_journal_entries
                WHERE scope = ? AND journal_date = ?
                ''',
                (scope, journal_date),
            ).fetchone()

        return self._row_to_entry(row) if row is not None else None

    def list(
        self,
        *,
        scope: str | None = None,
        limit: int = 30,
    ) -> list[BrainJournalEntry]:
        self.ensure_schema()
        params: list[object] = []

        query = "SELECT * FROM brain_journal_entries"
        if scope is not None:
            query += " WHERE scope = ?"
            params.append(scope)

        query += " ORDER BY journal_date DESC LIMIT ?"
        params.append(max(1, min(limit, 365)))

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row: sqlite3.Row) -> BrainJournalEntry:
        metrics_raw = json.loads(row["metrics_json"])
        learnings_raw = json.loads(row["learnings_json"])

        return BrainJournalEntry(
            journal_id=row["journal_id"],
            journal_date=row["journal_date"],
            scope=row["scope"],
            summary=row["summary"],
            metrics=[
                BrainJournalMetric(
                    name=item["name"],
                    value=item["value"],
                    unit=item.get("unit"),
                    previous_value=item.get("previous_value"),
                )
                for item in metrics_raw
            ],
            learnings=[
                BrainJournalLearning(
                    category=item["category"],
                    statement=item["statement"],
                    confidence=item["confidence"],
                    evidence_count=item.get("evidence_count", 0),
                )
                for item in learnings_raw
            ],
            corrections=json.loads(row["corrections_json"]),
            open_questions=json.loads(row["open_questions_json"]),
            metadata=json.loads(row["metadata_json"]),
        )
