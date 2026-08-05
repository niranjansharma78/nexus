from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import LearningCandidate, LearningDecision



class LearningRepository:
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
            CREATE TABLE IF NOT EXISTS learning_candidates (
                candidate_id TEXT PRIMARY KEY,
                source_label TEXT NOT NULL,
                target_label TEXT NOT NULL,
                relation TEXT NOT NULL,
                evidence_count INTEGER NOT NULL,
                confidence REAL NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                decision TEXT NOT NULL,
                rationale TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_candidate_identity
            ON learning_candidates(source_label, target_label, relation);
            """)

    def save(self, candidate: LearningCandidate) -> LearningCandidate:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute("""
            INSERT INTO learning_candidates (candidate_id, source_label, target_label, relation, evidence_count, confidence, first_seen, last_seen, decision, rationale, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_label, target_label, relation) DO UPDATE SET
              candidate_id=excluded.candidate_id, evidence_count=excluded.evidence_count, confidence=excluded.confidence, first_seen=excluded.first_seen, last_seen=excluded.last_seen, decision=excluded.decision, rationale=excluded.rationale, metadata_json=excluded.metadata_json
            """, (candidate.candidate_id, candidate.source_label, candidate.target_label, candidate.relation, candidate.evidence_count, candidate.confidence, candidate.first_seen, candidate.last_seen, candidate.decision.value, candidate.rationale, json.dumps(candidate.metadata)))
        return candidate

    def find(self, source_label: str, target_label: str, relation: str):
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM learning_candidates WHERE source_label=? AND target_label=? AND relation=?", (source_label, target_label, relation)).fetchone()
        return self._row(row) if row else None


    def list(
        self,
        *,
        decision: LearningDecision | str | None = None,
        limit: int = 100,
    ) -> list[LearningCandidate]:
        self.ensure_schema()

        params: list[object] = []
        query = "SELECT * FROM learning_candidates"

        if decision is not None:
            query += " WHERE decision = ?"
            params.append(
                decision.value
                if isinstance(decision, LearningDecision)
                else str(decision)
            )

        query += " ORDER BY confidence DESC, evidence_count DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [self._row(row) for row in rows]

    def decide(self, candidate_id: str, decision: LearningDecision):
        if decision == LearningDecision.PENDING:
            raise ValueError("Decision must be approved or rejected")
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute("UPDATE learning_candidates SET decision=? WHERE candidate_id=?", (decision.value, candidate_id))
            row = connection.execute("SELECT * FROM learning_candidates WHERE candidate_id=?", (candidate_id,)).fetchone()
        if row is None:
            raise KeyError(candidate_id)
        return self._row(row)

    @staticmethod
    def _row(row: sqlite3.Row) -> LearningCandidate:
        return LearningCandidate(candidate_id=row["candidate_id"], source_label=row["source_label"], target_label=row["target_label"], relation=row["relation"], evidence_count=row["evidence_count"], confidence=row["confidence"], first_seen=row["first_seen"], last_seen=row["last_seen"], decision=LearningDecision(row["decision"]), rationale=row["rationale"], metadata=json.loads(row["metadata_json"]))
