from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.brain.runtime_v2.service import CognitiveRuntimeV2

from .models import TriggerDispatchResult, TriggerEnvelope, TriggerKind
from .repository import TriggerRepository


class TriggerDispatcher:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.repository = TriggerRepository(self.database_path)
        self.runtime = CognitiveRuntimeV2(self.database_path)

    def submit(
        self,
        *,
        kind: TriggerKind | str,
        payload: dict[str, Any],
        world: str | None = None,
        source: str | None = None,
        objective: str | None = None,
        metadata: dict[str, Any] | None = None,
        process_now: bool = True,
    ) -> TriggerDispatchResult:
        trigger = TriggerEnvelope(
            kind=TriggerKind(kind),
            payload=dict(payload),
            world=world,
            source=source,
            objective=objective,
            metadata=dict(metadata or {}),
        )
        trigger.fingerprint = self._fingerprint(trigger)

        inserted = self.repository.insert_if_new(trigger)
        if not inserted:
            return TriggerDispatchResult(
                trigger_id=trigger.trigger_id,
                accepted=False,
                duplicate=True,
                succeeded=True,
            )

        if not process_now:
            return TriggerDispatchResult(
                trigger_id=trigger.trigger_id,
                accepted=True,
                succeeded=True,
            )

        return self._dispatch(trigger)

    def process_pending(self, *, limit: int = 100) -> list[TriggerDispatchResult]:
        return [
            self._dispatch(trigger)
            for trigger in self.repository.list_pending(limit=limit)
        ]

    def _dispatch(self, trigger: TriggerEnvelope) -> TriggerDispatchResult:
        try:
            if trigger.kind == TriggerKind.EVENT:
                runtime_result = self.runtime.run_from_event(
                    trigger.payload,
                    objective=trigger.objective,
                )
            else:
                objective = (
                    trigger.objective
                    or trigger.payload.get("objective")
                    or trigger.payload.get("title")
                    or trigger.payload.get("label")
                    or f"Process {trigger.kind.value}"
                )
                runtime_result = self.runtime.run(
                    trigger=trigger.kind.value,
                    objective=str(objective),
                    world=trigger.world or trigger.payload.get("world"),
                    context_query=str(
                        trigger.payload.get("context_query")
                        or trigger.payload.get("title")
                        or trigger.payload.get("label")
                        or objective
                    ),
                    metadata={
                        "source_trigger_id": trigger.trigger_id,
                        "source": trigger.source,
                        **trigger.metadata,
                    },
                )

            self.repository.mark_processed(
                trigger.trigger_id,
                runtime_run_id=runtime_result.run_id,
                error_text=(
                    "; ".join(runtime_result.errors)
                    if runtime_result.errors
                    else None
                ),
            )

            return TriggerDispatchResult(
                trigger_id=trigger.trigger_id,
                accepted=True,
                runtime_run_id=runtime_result.run_id,
                succeeded=runtime_result.succeeded,
                errors=list(runtime_result.errors),
                runtime_result=runtime_result.to_dict(),
            )
        except Exception as exc:
            self.repository.mark_processed(
                trigger.trigger_id,
                error_text=str(exc),
            )
            return TriggerDispatchResult(
                trigger_id=trigger.trigger_id,
                accepted=True,
                succeeded=False,
                errors=[str(exc)],
            )

    @staticmethod
    def _fingerprint(trigger: TriggerEnvelope) -> str:
        canonical = json.dumps(
            {
                "kind": trigger.kind.value,
                "payload": trigger.payload,
                "world": trigger.world,
                "source": trigger.source,
                "objective": trigger.objective,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
