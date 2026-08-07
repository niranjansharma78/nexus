from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .models import Prediction, PredictionOutcome, PredictionStatus

class PredictionRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                prediction_type TEXT NOT NULL,
                probability REAL NOT NULL,
                confidence REAL NOT NULL,
                horizon TEXT NOT NULL,
                expected_by TEXT,
                rationale TEXT NOT NULL,
                assumptions_json TEXT NOT NULL,
                evidence_ids_json TEXT NOT NULL,
                related_event_ids_json TEXT NOT NULL,
                world TEXT,
                status TEXT NOT NULL,
                outcome TEXT,
                resolved_at TEXT,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status);
            CREATE INDEX IF NOT EXISTS idx_predictions_world ON predictions(world);
            CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
            """)

    def save(self, p: Prediction) -> Prediction:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute("""
            INSERT INTO predictions (
                prediction_id,target,prediction_type,probability,confidence,horizon,
                expected_by,rationale,assumptions_json,evidence_ids_json,
                related_event_ids_json,world,status,outcome,resolved_at,created_at,metadata_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(prediction_id) DO UPDATE SET
                target=excluded.target,prediction_type=excluded.prediction_type,
                probability=excluded.probability,confidence=excluded.confidence,
                horizon=excluded.horizon,expected_by=excluded.expected_by,
                rationale=excluded.rationale,assumptions_json=excluded.assumptions_json,
                evidence_ids_json=excluded.evidence_ids_json,
                related_event_ids_json=excluded.related_event_ids_json,
                world=excluded.world,status=excluded.status,outcome=excluded.outcome,
                resolved_at=excluded.resolved_at,metadata_json=excluded.metadata_json
            """, (
                p.prediction_id,p.target,p.prediction_type,p.probability,p.confidence,
                p.horizon,p.expected_by,p.rationale,json.dumps(p.assumptions),
                json.dumps(p.evidence_ids),json.dumps(p.related_event_ids),p.world,
                p.status.value,p.outcome.value if p.outcome else None,p.resolved_at,
                p.created_at,json.dumps(p.metadata),
            ))
        return p

    def get(self, prediction_id: str) -> Prediction | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM predictions WHERE prediction_id=?", (prediction_id,)
            ).fetchone()
        return self._row(row) if row else None

    def list(self, *, status: PredictionStatus | str | None = None,
             world: str | None = None, prediction_type: str | None = None,
             limit: int = 100) -> list[Prediction]:
        self.ensure_schema()
        where, params = [], []
        if status is not None:
            where.append("status=?")
            params.append(PredictionStatus(status).value)
        if world is not None:
            where.append("world=?")
            params.append(world)
        if prediction_type is not None:
            where.append("prediction_type=?")
            params.append(prediction_type)
        query = "SELECT * FROM predictions"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> Prediction:
        return Prediction(
            prediction_id=row["prediction_id"],
            target=row["target"],
            prediction_type=row["prediction_type"],
            probability=float(row["probability"]),
            confidence=float(row["confidence"]),
            horizon=row["horizon"],
            expected_by=row["expected_by"],
            rationale=row["rationale"],
            assumptions=json.loads(row["assumptions_json"]),
            evidence_ids=json.loads(row["evidence_ids_json"]),
            related_event_ids=json.loads(row["related_event_ids_json"]),
            world=row["world"],
            status=PredictionStatus(row["status"]),
            outcome=PredictionOutcome(row["outcome"]) if row["outcome"] else None,
            resolved_at=row["resolved_at"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata_json"]),
        )
