from __future__ import annotations

from pathlib import Path

from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import UniversalEventRepository

from .models import CuriosityQuestion
from .repository import CuriosityRepository


class CuriosityEngine:
    def __init__(self, database_path: str | Path) -> None:
        self.event_repository = UniversalEventRepository(database_path)
        self.repository = CuriosityRepository(database_path)

    def discover_from_events(self, *, limit: int = 200) -> list[CuriosityQuestion]:
        questions: list[CuriosityQuestion] = []
        events = self.event_repository.list(limit=limit)

        for event in events:
            if event.transition == UniversalTransition.OBSERVED and event.confidence < 0.65:
                questions.append(
                    self.repository.save(
                        CuriosityQuestion(
                            question=f"What does '{event.object.label}' represent?",
                            reason="The event is only observed and confidence is low.",
                            priority=70,
                            confidence=event.confidence,
                            related_event_id=event.event_id,
                            related_evidence_id=event.evidence_id,
                            metadata={"trigger": "low_confidence_observation"},
                        )
                    )
                )

            if event.expected_next is None and not event.is_closed:
                questions.append(
                    self.repository.save(
                        CuriosityQuestion(
                            question=(
                                f"What should normally happen after "
                                f"'{event.object.label}'?"
                            ),
                            reason="The event is open but has no expected next transition.",
                            priority=60,
                            confidence=event.confidence,
                            related_event_id=event.event_id,
                            related_evidence_id=event.evidence_id,
                            metadata={"trigger": "missing_expected_next"},
                        )
                    )
                )

            if event.counterparty is None and event.object.kind in {
                "commitment",
                "transaction",
                "resource",
            }:
                questions.append(
                    self.repository.save(
                        CuriosityQuestion(
                            question=(
                                f"Who is the counterparty for "
                                f"'{event.object.label}'?"
                            ),
                            reason="A material event is missing a counterparty.",
                            priority=80,
                            confidence=event.confidence,
                            related_event_id=event.event_id,
                            related_evidence_id=event.evidence_id,
                            metadata={"trigger": "missing_counterparty"},
                        )
                    )
                )

        return questions
