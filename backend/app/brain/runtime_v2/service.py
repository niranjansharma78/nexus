from __future__ import annotations

from pathlib import Path
from typing import Any

from app.brain.orchestrator.models import OrchestrationRequest
from app.brain.orchestrator.service import CognitiveOrchestrator

from .models import RuntimeRunResult, RuntimeTrigger
from .policy import RuntimePolicy


class CognitiveRuntimeV2:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.orchestrator = CognitiveOrchestrator(self.database_path)
        self.policy = RuntimePolicy()

    def run(
        self,
        *,
        trigger: RuntimeTrigger | str,
        objective: str,
        world: str | None = None,
        intent: str | None = None,
        context_query: str | None = None,
        prediction_inputs: list[dict[str, Any]] | None = None,
        simulation_options: list[dict[str, Any]] | None = None,
        decision_options: list[dict[str, Any]] | None = None,
        plan_tasks: list[dict[str, Any]] | None = None,
        constraints: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        auto_execute_requested: bool = False,
    ) -> RuntimeRunResult:
        resolved_trigger = RuntimeTrigger(trigger)
        result = RuntimeRunResult(
            trigger=resolved_trigger,
            objective=objective,
        )

        try:
            request = OrchestrationRequest(
                objective=objective,
                world=world,
                intent=intent,
                context_query=context_query,
                prediction_inputs=list(prediction_inputs or []),
                simulation_options=list(simulation_options or []),
                decision_options=list(decision_options or []),
                plan_tasks=list(plan_tasks or []),
                constraints=list(constraints or []),
                metadata=dict(metadata or {}),
            )

            orchestration = self.orchestrator.run(request)
            result.orchestration = orchestration.to_dict()

            policy = self.policy.evaluate(
                world=world,
                has_plan=orchestration.plan is not None,
                auto_execute_requested=auto_execute_requested,
            )
            result.policy = policy
            result.requires_human_approval = bool(
                policy["approval_required"]
            )

            if orchestration.errors:
                result.errors.extend(orchestration.errors)

        except Exception as exc:
            result.errors.append(f"runtime_failed: {exc}")

        result.finish()
        return result

    def run_from_event(
        self,
        event: dict[str, Any],
        *,
        objective: str | None = None,
    ) -> RuntimeRunResult:
        label = (
            event.get("object", {}).get("label")
            if isinstance(event.get("object"), dict)
            else None
        ) or event.get("title") or "Respond to event"

        return self.run(
            trigger=RuntimeTrigger.EVENT,
            objective=objective or str(label),
            world=event.get("world"),
            context_query=str(label),
            metadata={
                "source_event_id": event.get("event_id"),
                "source": event.get("source"),
            },
        )
