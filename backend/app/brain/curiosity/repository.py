from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import CuriosityQuestion, CuriosityStatus


class CuriosityRepository:
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
                CREATE TABLE IF NOT EXISTS curiosity_questions (
                    question_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    scope TEXT NOT NULL,
                    related_event_id TEXT,
                    related_evidence_id INTEGER,
                    status TEXT NOT NULL,
                    answer TEXT,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    updated_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_curiosity_status
                    ON curiosity_questions(status);

                CREATE INDEX IF NOT EXISTS idx_curiosity_priority
                    ON curiosity_questions(priority DESC);
                '''
            )

    def save(self, item: CuriosityQuestion) -> CuriosityQuestion:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO curiosity_questions (
                    question_id, question, reason, priority, confidence,
                    scope, related_event_id, related_evidence_id,
                    status, answer, created_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(question_id) DO UPDATE SET
                    question=excluded.question,
                    reason=excluded.reason,
                    priority=excluded.priority,
                    confidence=excluded.confidence,
                    scope=excluded.scope,
                    related_event_id=excluded.related_event_id,
                    related_evidence_id=excluded.related_evidence_id,
                    status=excluded.status,
                    answer=excluded.answer,
                    metadata_json=excluded.metadata_json,
                    updated_at=CURRENT_TIMESTAMP
                ''',
                (
                    item.question_id,
                    item.question,
                    item.reason,
                    item.priority,
                    item.confidence,
                    item.scope,
                    item.related_event_id,
                    item.related_evidence_id,
                    item.status.value,
                    item.answer,
                    item.created_at,
                    json.dumps(item.metadata),
                ),
            )
        return item

    def list(
        self,
        *,
        status: CuriosityStatus | str | None = None,
        limit: int = 100,
    ) -> list[CuriosityQuestion]:
        self.ensure_schema()
        params: list[object] = []
        query = "SELECT * FROM curiosity_questions"

        if status is not None:
            query += " WHERE status=?"
            params.append(CuriosityStatus(status).value)

        query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._row(row) for row in rows]

    def answer(self, question_id: str, answer: str) -> CuriosityQuestion:
        if not answer.strip():
            raise ValueError("Answer is required")
        self.ensure_schema()
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                UPDATE curiosity_questions
                SET answer=?, status=?, updated_at=CURRENT_TIMESTAMP
                WHERE question_id=?
                ''',
                (answer.strip(), CuriosityStatus.ANSWERED.value, question_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(question_id)
            row = connection.execute(
                "SELECT * FROM curiosity_questions WHERE question_id=?",
                (question_id,),
            ).fetchone()
        return self._row(row)

    def dismiss(self, question_id: str) -> CuriosityQuestion:
        self.ensure_schema()
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                UPDATE curiosity_questions
                SET status=?, updated_at=CURRENT_TIMESTAMP
                WHERE question_id=?
                ''',
                (CuriosityStatus.DISMISSED.value, question_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(question_id)
            row = connection.execute(
                "SELECT * FROM curiosity_questions WHERE question_id=?",
                (question_id,),
            ).fetchone()
        return self._row(row)

    @staticmethod
    def _row(row: sqlite3.Row) -> CuriosityQuestion:
        return CuriosityQuestion(
            question_id=row["question_id"],
            question=row["question"],
            reason=row["reason"],
            priority=row["priority"],
            confidence=row["confidence"],
            scope=row["scope"],
            related_event_id=row["related_event_id"],
            related_evidence_id=row["related_evidence_id"],
            status=CuriosityStatus(row["status"]),
            answer=row["answer"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )
