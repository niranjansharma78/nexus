from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from .models import LearningCandidate, LearningDecision, RelationshipObservation
from .repository import LearningRepository

class LearningEngine:
    def __init__(self, database_path: str | Path, *, minimum_evidence: int = 2):
        if minimum_evidence < 1:
            raise ValueError("minimum_evidence must be at least 1")
        self.repository = LearningRepository(database_path)
        self.minimum_evidence = minimum_evidence

    @staticmethod
    def _aggregate_confidence(values: list[float]) -> float:
        remaining = 1.0
        for value in values:
            remaining *= 1.0 - max(0.0, min(value, 1.0))
        return round(1.0 - remaining, 10)

    def discover(self, observations: list[RelationshipObservation]):
        grouped = defaultdict(list)
        for item in observations:
            grouped[(item.source_label.strip(), item.target_label.strip(), item.relation.strip())].append(item)
        result=[]
        for (source, target, relation), items in grouped.items():
            if len(items) < self.minimum_evidence:
                continue
            existing = self.repository.find(source, target, relation)
            confidence = self._aggregate_confidence([item.confidence for item in items])
            first_seen=min(item.occurred_at for item in items)
            last_seen=max(item.occurred_at for item in items)
            evidence_ids=sorted({item.evidence_id for item in items if item.evidence_id is not None})
            candidate=LearningCandidate(
                candidate_id=existing.candidate_id if existing else LearningCandidate(source_label=source,target_label=target,relation=relation,evidence_count=len(items),confidence=confidence,first_seen=first_seen,last_seen=last_seen).candidate_id,
                source_label=source,target_label=target,relation=relation,evidence_count=len(items),confidence=confidence,first_seen=first_seen,last_seen=last_seen,
                decision=existing.decision if existing else LearningDecision.PENDING,
                rationale=f"Observed {len(items)} matching evidence item(s); combined confidence {confidence:.2f}.",
                metadata={"evidence_ids": evidence_ids},
            )
            self.repository.save(candidate)
            result.append(candidate)
        return sorted(result, key=lambda x: x.confidence, reverse=True)

    def approve(self, candidate_id: str):
        return self.repository.decide(candidate_id, LearningDecision.APPROVED)

    def reject(self, candidate_id: str):
        return self.repository.decide(candidate_id, LearningDecision.REJECTED)
