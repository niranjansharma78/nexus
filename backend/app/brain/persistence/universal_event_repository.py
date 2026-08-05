from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.brain.ontology.models import (
    UniversalEvent,
    UniversalObjectRef,
    ValueMeasure,
)
from app.brain.ontology.transitions import UniversalTransition


class UniversalEventRepository:
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
                CREATE TABLE IF NOT EXISTS universal_events (
                    event_id TEXT PRIMARY KEY,
                    object_json TEXT NOT NULL,
                    actor_json TEXT,
                    counterparty_json TEXT,
                    intent TEXT NOT NULL,
                    transition TEXT NOT NULL,
                    state TEXT NOT NULL,
                    world TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    evidence_id INTEGER,
                    expected_next TEXT,
                    closure TEXT NOT NULL,
                    organization_id TEXT,
                    domain_pack TEXT,
                    occurred_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_universal_events_transition
                    ON universal_events(transition);

                CREATE INDEX IF NOT EXISTS idx_universal_events_world
                    ON universal_events(world);

                CREATE INDEX IF NOT EXISTS idx_universal_events_closure
                    ON universal_events(closure);

                CREATE INDEX IF NOT EXISTS idx_universal_events_evidence
                    ON universal_events(evidence_id);
                '''
            )

    def save(self, event: UniversalEvent) -> UniversalEvent:
        self.ensure_schema()
        payload = event.to_dict()

        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO universal_events (
                    event_id,
                    object_json,
                    actor_json,
                    counterparty_json,
                    intent,
                    transition,
                    state,
                    world,
                    confidence,
                    source,
                    value_json,
                    evidence_id,
                    expected_next,
                    closure,
                    organization_id,
                    domain_pack,
                    occurred_at,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    object_json = excluded.object_json,
                    actor_json = excluded.actor_json,
                    counterparty_json = excluded.counterparty_json,
                    intent = excluded.intent,
                    transition = excluded.transition,
                    state = excluded.state,
                    world = excluded.world,
                    confidence = excluded.confidence,
                    source = excluded.source,
                    value_json = excluded.value_json,
                    evidence_id = excluded.evidence_id,
                    expected_next = excluded.expected_next,
                    closure = excluded.closure,
                    organization_id = excluded.organization_id,
                    domain_pack = excluded.domain_pack,
                    occurred_at = excluded.occurred_at,
                    metadata_json = excluded.metadata_json
                ''',
                (
                    event.event_id,
                    json.dumps(payload["object"]),
                    json.dumps(payload["actor"]) if payload["actor"] else None,
                    json.dumps(payload["counterparty"])
                    if payload["counterparty"]
                    else None,
                    event.intent,
                    event.transition.value,
                    event.state,
                    event.world,
                    event.confidence,
                    event.source,
                    json.dumps(payload["value"]),
                    event.evidence_id,
                    event.expected_next.value
                    if event.expected_next is not None
                    else None,
                    event.closure,
                    event.organization_id,
                    event.domain_pack,
                    event.occurred_at,
                    json.dumps(event.metadata),
                ),
            )

        return event

    def get(self, event_id: str) -> UniversalEvent | None:
        self.ensure_schema()

        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM universal_events
                WHERE event_id = ?
                ''',
                (event_id,),
            ).fetchone()

        return self._row_to_event(row) if row is not None else None

    def list(
        self,
        *,
        limit: int = 100,
        world: str | None = None,
        closure: str | None = None,
        transition: UniversalTransition | str | None = None,
        evidence_id: int | None = None,
    ) -> list[UniversalEvent]:
        self.ensure_schema()
        where: list[str] = []
        parameters: list[Any] = []

        if world is not None:
            where.append("world = ?")
            parameters.append(world)

        if closure is not None:
            where.append("closure = ?")
            parameters.append(closure)

        if transition is not None:
            where.append("transition = ?")
            parameters.append(UniversalTransition(transition).value)

        if evidence_id is not None:
            where.append("evidence_id = ?")
            parameters.append(evidence_id)

        query = "SELECT * FROM universal_events"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY occurred_at DESC, created_at DESC LIMIT ?"
        parameters.append(max(1, min(int(limit), 500)))

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_event(row) for row in rows]

    def count(
        self,
        *,
        world: str | None = None,
        closure: str | None = None,
    ) -> int:
        self.ensure_schema()
        where: list[str] = []
        parameters: list[Any] = []

        if world is not None:
            where.append("world = ?")
            parameters.append(world)

        if closure is not None:
            where.append("closure = ?")
            parameters.append(closure)

        query = "SELECT COUNT(*) AS count FROM universal_events"
        if where:
            query += " WHERE " + " AND ".join(where)

        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()

        return int(row["count"])

    def delete(self, event_id: str) -> bool:
        self.ensure_schema()

        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM universal_events WHERE event_id = ?",
                (event_id,),
            )

        return cursor.rowcount > 0

    @staticmethod
    def _object_ref_from_json(value: str | None) -> UniversalObjectRef | None:
        if value is None:
            return None

        data = json.loads(value)
        return UniversalObjectRef(
            kind=data["kind"],
            label=data["label"],
            external_id=data.get("external_id"),
            attributes=data.get("attributes") or {},
        )

    @staticmethod
    def _value_from_json(value: str) -> ValueMeasure:
        data = json.loads(value)
        return ValueMeasure(
            amount=data.get("amount"),
            currency=data.get("currency"),
            quantity=data.get("quantity"),
            unit=data.get("unit"),
            importance=data.get("importance"),
        )

    def _row_to_event(self, row: sqlite3.Row) -> UniversalEvent:
        return UniversalEvent(
            event_id=row["event_id"],
            object=self._object_ref_from_json(row["object_json"]),
            actor=self._object_ref_from_json(row["actor_json"]),
            counterparty=self._object_ref_from_json(
                row["counterparty_json"]
            ),
            intent=row["intent"],
            transition=UniversalTransition(row["transition"]),
            state=row["state"],
            world=row["world"],
            confidence=float(row["confidence"]),
            source=row["source"],
            value=self._value_from_json(row["value_json"]),
            evidence_id=row["evidence_id"],
            expected_next=(
                UniversalTransition(row["expected_next"])
                if row["expected_next"] is not None
                else None
            ),
            closure=row["closure"],
            organization_id=row["organization_id"],
            domain_pack=row["domain_pack"],
            occurred_at=row["occurred_at"],
            metadata=json.loads(row["metadata_json"]),
        )
