from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import UniversalEvidence


class EvidenceRepository:
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
                CREATE TABLE IF NOT EXISTS universal_evidence (
                    evidence_uid TEXT PRIMARY KEY,
                    connector TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    author TEXT,
                    payload_json TEXT NOT NULL,
                    attachments_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_universal_evidence_connector
                    ON universal_evidence(connector);

                CREATE INDEX IF NOT EXISTS idx_universal_evidence_observed
                    ON universal_evidence(observed_at);
                '''
            )

    def save_if_new(self, evidence: UniversalEvidence) -> bool:
        self.ensure_schema()

        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT OR IGNORE INTO universal_evidence (
                    evidence_uid,
                    connector,
                    evidence_type,
                    observed_at,
                    source,
                    author,
                    payload_json,
                    attachments_json,
                    metadata_json,
                    confidence,
                    fingerprint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    evidence.evidence_uid,
                    evidence.connector,
                    evidence.evidence_type,
                    evidence.observed_at,
                    evidence.source,
                    evidence.author,
                    json.dumps(evidence.payload),
                    json.dumps(list(evidence.attachments)),
                    json.dumps(evidence.metadata),
                    evidence.confidence,
                    evidence.fingerprint,
                ),
            )

        return cursor.rowcount > 0

    def count(self) -> int:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM universal_evidence"
            ).fetchone()
        return int(row["count"])
