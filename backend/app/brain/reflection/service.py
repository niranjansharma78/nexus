from __future__ import annotations

from pathlib import Path

from .models import ReflectionRecord
from .repository import ReflectionRepository


class ReflectionEngine:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.repository = (
            ReflectionRepository(database_path)
            if database_path is not None
            else None
        )

    def reflect(
        self,
        *,
        subject: str,
        expected: str,
        actual: str,
        lesson: str,
        confidence_before: float,
        confidence_after: float,
        world: str | None = None,
        prediction_id: str | None = None,
        simulation_id: str | None = None,
        chosen_option_id: str | None = None,
        recommended_option_id: str | None = None,
        assumption_failures: list[str] | None = None,
        evidence_ids: list[int] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ReflectionRecord:
        record = ReflectionRecord(
            subject=subject,
            expected=expected,
            actual=actual,
            lesson=lesson,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            world=world,
            prediction_id=prediction_id,
            simulation_id=simulation_id,
            chosen_option_id=chosen_option_id,
            recommended_option_id=recommended_option_id,
            assumption_failures=list(assumption_failures or []),
            evidence_ids=list(evidence_ids or []),
            metadata=dict(metadata or {}),
        )

        if self.repository is not None:
            self.repository.save(record)

        return record

    def outcome_alignment(self, record: ReflectionRecord) -> dict[str, object]:
        recommendation_followed = (
            bool(record.recommended_option_id)
            and record.recommended_option_id == record.chosen_option_id
        )

        return {
            "reflection_id": record.reflection_id,
            "recommendation_followed": recommendation_followed,
            "confidence_delta": record.confidence_delta,
            "assumption_failure_count": len(record.assumption_failures),
            "lesson": record.lesson,
        }
