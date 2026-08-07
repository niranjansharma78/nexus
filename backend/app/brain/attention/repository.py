from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import AttentionItem, AttentionPriority


class AttentionRepository:
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
                CREATE TABLE IF NOT EXISTS attention_items (
                    item_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    importance REAL NOT NULL,
                    urgency REAL NOT NULL,
                    novelty REAL NOT NULL,
                    relevance REAL NOT NULL,
                    risk REAL NOT NULL,
                    confidence REAL NOT NULL,
                    world TEXT,
                    source TEXT,
                    reference_id TEXT,
                    attention_score REAL NOT NULL,
                    priority TEXT NOT NULL,
                    should_escalate INTEGER NOT NULL,
                    should_process_now INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                '''
            )

    def save(self, item: AttentionItem) -> AttentionItem:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT OR REPLACE INTO attention_items (
                    item_id, label, importance, urgency, novelty,
                    relevance, risk, confidence, world, source,
                    reference_id, attention_score, priority,
                    should_escalate, should_process_now, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    item.item_id,
                    item.label,
                    item.importance,
                    item.urgency,
                    item.novelty,
                    item.relevance,
                    item.risk,
                    item.confidence,
                    item.world,
                    item.source,
                    item.reference_id,
                    item.attention_score,
                    item.priority.value,
                    1 if item.should_escalate else 0,
                    1 if item.should_process_now else 0,
                    json.dumps(item.metadata),
                ),
            )
        return item

    def list(self, *, limit: int = 100) -> list[AttentionItem]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM attention_items
                ORDER BY attention_score DESC
                LIMIT ?
                ''',
                (max(1, min(int(limit), 500)),),
            ).fetchall()

        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> AttentionItem:
        return AttentionItem(
            item_id=row["item_id"],
            label=row["label"],
            importance=float(row["importance"]),
            urgency=float(row["urgency"]),
            novelty=float(row["novelty"]),
            relevance=float(row["relevance"]),
            risk=float(row["risk"]),
            confidence=float(row["confidence"]),
            world=row["world"],
            source=row["source"],
            reference_id=row["reference_id"],
            attention_score=float(row["attention_score"]),
            priority=AttentionPriority(row["priority"]),
            should_escalate=bool(row["should_escalate"]),
            should_process_now=bool(row["should_process_now"]),
            metadata=json.loads(row["metadata_json"]),
        )
