from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Plan, PlanStatus, PlanTask, TaskStatus


class PlanRepository:
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
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    tasks_json TEXT NOT NULL,
                    world TEXT,
                    decision_refs_json TEXT NOT NULL,
                    simulation_refs_json TEXT NOT NULL,
                    constraints_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL,
                    critical_path_json TEXT NOT NULL,
                    replanning_required INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                '''
            )

    def save(self, plan: Plan) -> Plan:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO plans (
                    plan_id, objective, tasks_json, world,
                    decision_refs_json, simulation_refs_json,
                    constraints_json, status, progress,
                    critical_path_json, replanning_required,
                    created_at, updated_at, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(plan_id) DO UPDATE SET
                    tasks_json=excluded.tasks_json,
                    status=excluded.status,
                    progress=excluded.progress,
                    critical_path_json=excluded.critical_path_json,
                    replanning_required=excluded.replanning_required,
                    updated_at=excluded.updated_at,
                    metadata_json=excluded.metadata_json
                ''',
                (
                    plan.plan_id,
                    plan.objective,
                    json.dumps([task.to_dict() for task in plan.tasks]),
                    plan.world,
                    json.dumps(plan.decision_refs),
                    json.dumps(plan.simulation_refs),
                    json.dumps(plan.constraints),
                    plan.status.value,
                    plan.progress,
                    json.dumps(plan.critical_path),
                    1 if plan.replanning_required else 0,
                    plan.created_at,
                    plan.updated_at,
                    json.dumps(plan.metadata),
                ),
            )
        return plan

    def get(self, plan_id: str) -> Plan | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM plans WHERE plan_id=?",
                (plan_id,),
            ).fetchone()
        return self._row(row) if row else None

    def list(self, *, limit: int = 100) -> list[Plan]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM plans
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (max(1, min(int(limit), 500)),),
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> Plan:
        tasks = [
            PlanTask(
                title=item["title"],
                owner=item.get("owner"),
                due_at=item.get("due_at"),
                duration_hours=float(item.get("duration_hours", 1.0)),
                dependencies=item.get("dependencies", []),
                status=TaskStatus(item.get("status", "pending")),
                priority=float(item.get("priority", 0.5)),
                progress=float(item.get("progress", 0.0)),
                task_id=item["task_id"],
                metadata=item.get("metadata", {}),
            )
            for item in json.loads(row["tasks_json"])
        ]

        return Plan(
            plan_id=row["plan_id"],
            objective=row["objective"],
            tasks=tasks,
            world=row["world"],
            decision_refs=json.loads(row["decision_refs_json"]),
            simulation_refs=json.loads(row["simulation_refs_json"]),
            constraints=json.loads(row["constraints_json"]),
            status=PlanStatus(row["status"]),
            progress=float(row["progress"]),
            critical_path=json.loads(row["critical_path_json"]),
            replanning_required=bool(row["replanning_required"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata_json"]),
        )
