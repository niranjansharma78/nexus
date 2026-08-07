from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ReflectionRecord, ReflectionStatus


class ReflectionRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS reflections (
                    reflection_id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    expected TEXT NOT NULL,
                    actual TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    confidence_before REAL NOT NULL,
                    confidence_after REAL NOT NULL,
                    world TEXT,
                    prediction_id TEXT,
                    simulation_id TEXT,
                    chosen_option_id TEXT,
                    recommended_option_id TEXT,
                    assumption_failures_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                '''
            )

    def save(self, record: ReflectionRecord) -> ReflectionRecord:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT OR REPLACE INTO reflections (
                    reflection_id, subject, expected, actual, lesson,
                    confidence_before, confidence_after, world,
                    prediction_id, simulation_id, chosen_option_id,
                    recommended_option_id, assumption_failures_json,
                    evidence_ids_json, status, created_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record.reflection_id,
                    record.subject,
                    record.expected,
                    record.actual,
                    record.lesson,
                    record.confidence_before,
                    record.confidence_after,
                    record.world,
                    record.prediction_id,
                    record.simulation_id,
                    record.chosen_option_id,
                    record.recommended_option_id,
                    json.dumps(record.assumption_failures),
                    json.dumps(record.evidence_ids),
                    record.status.value,
                    record.created_at,
                    json.dumps(record.metadata),
                ),
            )
        return record

    def get(self, reflection_id: str) -> ReflectionRecord | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM reflections WHERE reflection_id=?",
                (reflection_id,),
            ).fetchone()
        return self._row(row) if row else None

    def list(self, *, limit: int = 100) -> list[ReflectionRecord]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM reflections
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (max(1, min(int(limit), 500)),),
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> ReflectionRecord:
        return ReflectionRecord(
            reflection_id=row["reflection_id"],
            subject=row["subject"],
            expected=row["expected"],
            actual=row["actual"],
            lesson=row["lesson"],
            confidence_before=float(row["confidence_before"]),
            confidence_after=float(row["confidence_after"]),
            world=row["world"],
            prediction_id=row["prediction_id"],
            simulation_id=row["simulation_id"],
            chosen_option_id=row["chosen_option_id"],
            recommended_option_id=row["recommended_option_id"],
            assumption_failures=json.loads(row["assumption_failures_json"]),
            evidence_ids=json.loads(row["evidence_ids_json"]),
            status=ReflectionStatus(row["status"]),
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )
