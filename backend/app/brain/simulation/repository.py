from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Simulation, SimulationOption, SimulationOutcome, SimulationStatus


class SimulationRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS simulations (
                simulation_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                current_state_json TEXT NOT NULL,
                options_json TEXT NOT NULL,
                horizon TEXT NOT NULL,
                world TEXT,
                constraints_json TEXT NOT NULL,
                assumptions_json TEXT NOT NULL,
                external_predictions_json TEXT NOT NULL,
                status TEXT NOT NULL,
                recommended_option_id TEXT,
                ranking_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                metadata_json TEXT NOT NULL
            )''')

    def save(self, simulation: Simulation) -> Simulation:
        self.ensure_schema()
        with self._connect() as connection:
            connection.execute('''INSERT INTO simulations (
                simulation_id, objective, current_state_json, options_json, horizon, world,
                constraints_json, assumptions_json, external_predictions_json, status,
                recommended_option_id, ranking_json, created_at, completed_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(simulation_id) DO UPDATE SET
                status=excluded.status,
                recommended_option_id=excluded.recommended_option_id,
                ranking_json=excluded.ranking_json,
                completed_at=excluded.completed_at,
                metadata_json=excluded.metadata_json''', (
                simulation.simulation_id,
                simulation.objective,
                json.dumps(simulation.current_state),
                json.dumps([option.to_dict() for option in simulation.options]),
                simulation.horizon,
                simulation.world,
                json.dumps(simulation.constraints),
                json.dumps(simulation.assumptions),
                json.dumps(simulation.external_predictions),
                simulation.status.value,
                simulation.recommended_option_id,
                json.dumps(simulation.ranking),
                simulation.created_at,
                simulation.completed_at,
                json.dumps(simulation.metadata),
            ))
        return simulation

    def get(self, simulation_id: str) -> Simulation | None:
        self.ensure_schema()
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM simulations WHERE simulation_id=?", (simulation_id,)).fetchone()
        return self._row(row) if row else None

    def list(self, *, limit: int = 100) -> list[Simulation]:
        self.ensure_schema()
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM simulations ORDER BY created_at DESC LIMIT ?", (max(1, min(int(limit), 500)),)).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> Simulation:
        raw_options = json.loads(row["options_json"])
        options = []
        for raw in raw_options:
            outcomes = [SimulationOutcome(**item) for item in raw.get("outcomes", [])]
            options.append(SimulationOption(
                option_id=raw["option_id"],
                label=raw["label"],
                outcomes=outcomes,
                cost_score=raw.get("cost_score", 0.0),
                complexity_score=raw.get("complexity_score", 0.0),
                reversibility=raw.get("reversibility", 0.5),
                constraint_violations=raw.get("constraint_violations", []),
                assumptions=raw.get("assumptions", []),
                metadata=raw.get("metadata", {}),
            ))
        return Simulation(
            simulation_id=row["simulation_id"], objective=row["objective"], current_state=json.loads(row["current_state_json"]),
            options=options, horizon=row["horizon"], world=row["world"], constraints=json.loads(row["constraints_json"]),
            assumptions=json.loads(row["assumptions_json"]), external_predictions=json.loads(row["external_predictions_json"]),
            status=SimulationStatus(row["status"]), recommended_option_id=row["recommended_option_id"], ranking=json.loads(row["ranking_json"]),
            created_at=row["created_at"], completed_at=row["completed_at"], metadata=json.loads(row["metadata_json"]),
        )
