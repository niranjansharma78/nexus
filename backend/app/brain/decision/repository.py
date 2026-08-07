from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import DecisionOption, DecisionRecord, DecisionStatus


class DecisionRepository:
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
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    options_json TEXT NOT NULL,
                    recommended_option_id TEXT,
                    ranking_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    rationale TEXT NOT NULL,
                    world TEXT,
                    intent TEXT,
                    context_summary_json TEXT NOT NULL,
                    prediction_refs_json TEXT NOT NULL,
                    simulation_refs_json TEXT NOT NULL,
                    constraints_json TEXT NOT NULL,
                    chosen_option_id TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    metadata_json TEXT NOT NULL
                )
                '''
            )

    def save(self, record: DecisionRecord) -> DecisionRecord:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO decisions (
                    decision_id, objective, options_json,
                    recommended_option_id, ranking_json, confidence,
                    rationale, world, intent, context_summary_json,
                    prediction_refs_json, simulation_refs_json,
                    constraints_json, chosen_option_id, status,
                    created_at, resolved_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(decision_id) DO UPDATE SET
                    recommended_option_id=excluded.recommended_option_id,
                    ranking_json=excluded.ranking_json,
                    confidence=excluded.confidence,
                    rationale=excluded.rationale,
                    chosen_option_id=excluded.chosen_option_id,
                    status=excluded.status,
                    resolved_at=excluded.resolved_at,
                    metadata_json=excluded.metadata_json
                ''',
                (
                    record.decision_id,
                    record.objective,
                    json.dumps([item.to_dict() for item in record.options]),
                    record.recommended_option_id,
                    json.dumps(record.ranking),
                    record.confidence,
                    record.rationale,
                    record.world,
                    record.intent,
                    json.dumps(record.context_summary),
                    json.dumps(record.prediction_refs),
                    json.dumps(record.simulation_refs),
                    json.dumps(record.constraints),
                    record.chosen_option_id,
                    record.status.value,
                    record.created_at,
                    record.resolved_at,
                    json.dumps(record.metadata),
                ),
            )
        return record

    def get(self, decision_id: str) -> DecisionRecord | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM decisions WHERE decision_id=?",
                (decision_id,),
            ).fetchone()
        return self._row(row) if row else None

    def list(self, *, limit: int = 100) -> list[DecisionRecord]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM decisions
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (max(1, min(int(limit), 500)),),
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> DecisionRecord:
        options = [
            DecisionOption(**item)
            for item in json.loads(row["options_json"])
        ]

        return DecisionRecord(
            decision_id=row["decision_id"],
            objective=row["objective"],
            options=options,
            recommended_option_id=row["recommended_option_id"],
            ranking=json.loads(row["ranking_json"]),
            confidence=float(row["confidence"]),
            rationale=row["rationale"],
            world=row["world"],
            intent=row["intent"],
            context_summary=json.loads(row["context_summary_json"]),
            prediction_refs=json.loads(row["prediction_refs_json"]),
            simulation_refs=json.loads(row["simulation_refs_json"]),
            constraints=json.loads(row["constraints_json"]),
            chosen_option_id=row["chosen_option_id"],
            status=DecisionStatus(row["status"]),
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
            metadata=json.loads(row["metadata_json"]),
        )
