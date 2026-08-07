from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import DecisionOption, DecisionRecord, DecisionStatus
from .repository import DecisionRepository


class DecisionEngine:
    def __init__(
        self,
        database_path: str | Path | None = None,
    ) -> None:
        self.repository = (
            DecisionRepository(database_path)
            if database_path is not None
            else None
        )

    def decide(
        self,
        *,
        objective: str,
        options: list[DecisionOption],
        world: str | None = None,
        intent: str | None = None,
        context_summary: dict[str, object] | None = None,
        prediction_refs: list[str] | None = None,
        simulation_refs: list[str] | None = None,
        constraints: list[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> DecisionRecord:
        if not objective.strip():
            raise ValueError("objective is required")
        if not options:
            raise ValueError("At least one option is required")

        ranking = [
            self._score_option(option)
            for option in options
        ]
        ranking.sort(key=lambda item: item["score"], reverse=True)

        feasible = [item for item in ranking if item["feasible"]]
        recommended = feasible[0]["option_id"] if feasible else None

        confidence = 0.0
        if feasible:
            confidence = round(
                sum(float(item["confidence"]) for item in feasible)
                / len(feasible),
                10,
            )

        rationale = self._build_rationale(
            objective=objective,
            ranking=ranking,
            recommended_option_id=recommended,
            intent=intent,
        )

        record = DecisionRecord(
            objective=objective,
            options=options,
            recommended_option_id=recommended,
            ranking=ranking,
            confidence=confidence,
            rationale=rationale,
            world=world,
            intent=intent,
            context_summary=dict(context_summary or {}),
            prediction_refs=list(prediction_refs or []),
            simulation_refs=list(simulation_refs or []),
            constraints=list(constraints or []),
            metadata=dict(metadata or {}),
        )

        if self.repository is not None:
            self.repository.save(record)

        return record

    def choose(
        self,
        decision_id: str,
        option_id: str,
        *,
        approve: bool = True,
    ) -> DecisionRecord:
        if self.repository is None:
            raise RuntimeError("Repository required for choice persistence")

        record = self.repository.get(decision_id)
        if record is None:
            raise KeyError(f"Decision not found: {decision_id}")

        valid_ids = {item.option_id for item in record.options}
        if option_id not in valid_ids:
            raise ValueError(f"Unknown option: {option_id}")

        record.chosen_option_id = option_id
        record.status = (
            DecisionStatus.APPROVED
            if approve
            else DecisionStatus.REJECTED
        )
        record.resolved_at = datetime.now(timezone.utc).isoformat()
        self.repository.save(record)
        return record

    @staticmethod
    def _score_option(option: DecisionOption) -> dict[str, object]:
        if option.constraint_violations:
            return {
                "option_id": option.option_id,
                "label": option.label,
                "score": 0.0,
                "feasible": False,
                "confidence": option.confidence,
                "constraint_violations": list(
                    option.constraint_violations
                ),
            }

        score = (
            option.expected_value * 0.40
            + (1.0 - option.expected_risk) * 0.25
            + option.confidence * 0.15
            + option.reversibility * 0.10
            + (1.0 - option.cost_score) * 0.05
            + (1.0 - option.complexity_score) * 0.05
        )

        return {
            "option_id": option.option_id,
            "label": option.label,
            "score": round(max(0.0, min(score, 1.0)), 10),
            "feasible": True,
            "confidence": option.confidence,
            "constraint_violations": [],
        }

    @staticmethod
    def _build_rationale(
        *,
        objective: str,
        ranking: list[dict[str, object]],
        recommended_option_id: str | None,
        intent: str | None,
    ) -> str:
        if recommended_option_id is None:
            return (
                f"No feasible option could be recommended for '{objective}'."
            )

        top = next(
            item
            for item in ranking
            if item["option_id"] == recommended_option_id
        )
        intent_text = f" for intent '{intent}'" if intent else ""

        return (
            f"Recommended '{top['label']}'{intent_text} because it achieved "
            f"the highest feasible composite score ({top['score']})."
        )
