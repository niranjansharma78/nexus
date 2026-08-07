from __future__ import annotations

from pathlib import Path
from typing import Any

from app.brain.context_engine.service import ContextEngine
from app.brain.decision.models import DecisionOption
from app.brain.decision.service import DecisionEngine
from app.brain.planning.models import PlanTask
from app.brain.planning.service import PlanningEngine
from app.brain.prediction.service import PredictionEngine
from app.brain.simulation.models import SimulationOption, SimulationOutcome
from app.brain.simulation.service import SimulationEngine

from .models import OrchestrationRequest, OrchestrationResult


class CognitiveOrchestrator:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def run(self, request: OrchestrationRequest) -> OrchestrationResult:
        result = OrchestrationResult(objective=request.objective)

        context_data = None
        if request.context_query:
            try:
                context_data = ContextEngine(self.database_path).build(
                    request.context_query,
                    world=request.world,
                ).to_dict()
                result.context = context_data
                result.trace.append({
                    "stage": "context",
                    "status": "ok",
                })
            except Exception as exc:
                result.errors.append(f"context_failed: {exc}")
                result.trace.append({
                    "stage": "context",
                    "status": "failed",
                    "error": str(exc),
                })

        prediction_refs: list[str] = []
        if request.prediction_inputs:
            prediction_engine = PredictionEngine(self.database_path)

            for payload in request.prediction_inputs:
                try:
                    prediction = prediction_engine.create(
                        target=str(payload["target"]),
                        prediction_type=str(payload["prediction_type"]),
                        probability=float(payload["probability"]),
                        confidence=float(payload["confidence"]),
                        horizon=str(payload["horizon"]),
                        expected_by=payload.get("expected_by"),
                        rationale=str(payload.get("rationale", "")),
                        assumptions=list(payload.get("assumptions", [])),
                        evidence_ids=list(payload.get("evidence_ids", [])),
                        related_event_ids=list(
                            payload.get("related_event_ids", [])
                        ),
                        world=payload.get("world", request.world),
                        metadata=dict(payload.get("metadata", {})),
                    )
                    prediction_refs.append(prediction.prediction_id)
                    result.predictions.append(prediction.to_dict())
                except Exception as exc:
                    result.errors.append(f"prediction_failed: {exc}")

            result.trace.append({
                "stage": "prediction",
                "status": "ok" if prediction_refs else "skipped_or_failed",
                "count": len(prediction_refs),
            })

        simulation_ref = None
        if request.simulation_options:
            try:
                options = [
                    self._simulation_option(item)
                    for item in request.simulation_options
                ]
                simulation = SimulationEngine(
                    self.database_path
                ).create_and_run(
                    objective=request.objective,
                    current_state={
                        "context": context_data or {},
                    },
                    options=options,
                    horizon=str(
                        request.metadata.get("horizon", "30d")
                    ),
                    world=request.world,
                    constraints=request.constraints,
                    external_predictions=result.predictions,
                )
                simulation_ref = simulation.simulation_id
                result.simulation = simulation.to_dict()
                result.trace.append({
                    "stage": "simulation",
                    "status": "ok",
                    "simulation_id": simulation_ref,
                })
            except Exception as exc:
                result.errors.append(f"simulation_failed: {exc}")
                result.trace.append({
                    "stage": "simulation",
                    "status": "failed",
                    "error": str(exc),
                })

        decision_ref = None
        if request.decision_options:
            try:
                decision_options = [
                    DecisionOption(**item)
                    for item in request.decision_options
                ]
                decision = DecisionEngine(
                    self.database_path
                ).decide(
                    objective=request.objective,
                    options=decision_options,
                    world=request.world,
                    intent=request.intent,
                    context_summary=(
                        (context_data or {}).get("summary", {})
                    ),
                    prediction_refs=prediction_refs,
                    simulation_refs=(
                        [simulation_ref] if simulation_ref else []
                    ),
                    constraints=request.constraints,
                )
                decision_ref = decision.decision_id
                result.decision = decision.to_dict()
                result.trace.append({
                    "stage": "decision",
                    "status": "ok",
                    "decision_id": decision_ref,
                })
            except Exception as exc:
                result.errors.append(f"decision_failed: {exc}")
                result.trace.append({
                    "stage": "decision",
                    "status": "failed",
                    "error": str(exc),
                })

        if request.plan_tasks:
            try:
                tasks = [
                    PlanTask(**item)
                    for item in request.plan_tasks
                ]
                plan = PlanningEngine(
                    self.database_path
                ).create_plan(
                    objective=request.objective,
                    tasks=tasks,
                    world=request.world,
                    decision_refs=(
                        [decision_ref] if decision_ref else []
                    ),
                    simulation_refs=(
                        [simulation_ref] if simulation_ref else []
                    ),
                    constraints=request.constraints,
                )
                result.plan = plan.to_dict()
                result.trace.append({
                    "stage": "planning",
                    "status": "ok",
                    "plan_id": plan.plan_id,
                })
            except Exception as exc:
                result.errors.append(f"planning_failed: {exc}")
                result.trace.append({
                    "stage": "planning",
                    "status": "failed",
                    "error": str(exc),
                })

        result.finish()
        return result

    @staticmethod
    def _simulation_option(payload: dict[str, Any]) -> SimulationOption:
        outcomes = [
            SimulationOutcome(**item)
            for item in payload.get("outcomes", [])
        ]

        return SimulationOption(
            option_id=str(payload["option_id"]),
            label=str(payload["label"]),
            outcomes=outcomes,
            cost_score=float(payload.get("cost_score", 0.0)),
            complexity_score=float(
                payload.get("complexity_score", 0.0)
            ),
            reversibility=float(payload.get("reversibility", 0.5)),
            constraint_violations=list(
                payload.get("constraint_violations", [])
            ),
            assumptions=list(payload.get("assumptions", [])),
            metadata=dict(payload.get("metadata", {})),
        )
