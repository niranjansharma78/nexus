from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import Simulation, SimulationOption, SimulationStatus
from .repository import SimulationRepository


class SimulationEngine:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.repository = SimulationRepository(database_path) if database_path is not None else None

    def run(self, simulation: Simulation) -> Simulation:
        ranking = [self._score_option(option) for option in simulation.options]
        ranking.sort(key=lambda item: item["score"], reverse=True)
        simulation.ranking = ranking
        simulation.recommended_option_id = ranking[0]["option_id"] if ranking else None
        simulation.status = SimulationStatus.COMPLETED
        simulation.completed_at = datetime.now(timezone.utc).isoformat()
        if self.repository is not None:
            self.repository.save(simulation)
        return simulation

    def create_and_run(self, *, objective: str, current_state: dict[str, object], options: list[SimulationOption], horizon: str, world: str | None = None, constraints: list[str] | None = None, assumptions: list[str] | None = None, external_predictions: list[dict[str, object]] | None = None, metadata: dict[str, object] | None = None) -> Simulation:
        return self.run(Simulation(
            objective=objective,
            current_state=dict(current_state),
            options=options,
            horizon=horizon,
            world=world,
            constraints=list(constraints or []),
            assumptions=list(assumptions or []),
            external_predictions=[dict(item) for item in (external_predictions or [])],
            metadata=dict(metadata or {}),
        ))

    @staticmethod
    def _score_option(option: SimulationOption) -> dict[str, object]:
        if option.constraint_violations:
            return {"option_id": option.option_id, "label": option.label, "score": 0.0, "expected_value": 0.0, "expected_risk": 1.0, "confidence": 1.0, "feasible": False, "constraint_violations": list(option.constraint_violations)}
        if not option.outcomes:
            return {"option_id": option.option_id, "label": option.label, "score": 0.0, "expected_value": 0.0, "expected_risk": 0.0, "confidence": 0.0, "feasible": True, "constraint_violations": []}
        total = sum(item.probability for item in option.outcomes) or 1.0
        expected_value = sum(item.probability * item.value_score for item in option.outcomes) / total
        expected_risk = sum(item.probability * item.risk_score for item in option.outcomes) / total
        confidence = sum(item.probability * item.confidence for item in option.outcomes) / total
        score = expected_value * 0.45 + (1.0 - expected_risk) * 0.25 + confidence * 0.15 + option.reversibility * 0.10 + (1.0 - option.cost_score) * 0.03 + (1.0 - option.complexity_score) * 0.02
        return {"option_id": option.option_id, "label": option.label, "score": round(max(0.0, min(score, 1.0)), 10), "expected_value": round(expected_value, 10), "expected_risk": round(expected_risk, 10), "confidence": round(confidence, 10), "feasible": True, "constraint_violations": []}
