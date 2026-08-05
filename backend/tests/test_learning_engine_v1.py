from pathlib import Path
from app.brain.learning.models import LearningDecision, RelationshipObservation
from app.brain.learning.service import LearningEngine

def obs(evidence_id: int, confidence: float = 0.6):
    return RelationshipObservation(source_label="Supplier A", target_label="Company B", relation="supplies", confidence=confidence, evidence_id=evidence_id)

def test_single_observation_does_not_create_candidate(tmp_path: Path):
    assert LearningEngine(tmp_path / "brain.db").discover([obs(1)]) == []

def test_repeated_evidence_creates_candidate(tmp_path: Path):
    candidate = LearningEngine(tmp_path / "brain.db").discover([obs(1,0.6), obs(2,0.7)])[0]
    assert candidate.evidence_count == 2
    assert candidate.confidence == 0.88
    assert candidate.metadata["evidence_ids"] == [1,2]

def test_more_evidence_increases_confidence(tmp_path: Path):
    engine=LearningEngine(tmp_path / "brain.db")
    first=engine.discover([obs(1,0.5),obs(2,0.5)])[0]
    second=engine.discover([obs(1,0.5),obs(2,0.5),obs(3,0.5)])[0]
    assert first.confidence == 0.75
    assert second.confidence == 0.875
    assert first.candidate_id == second.candidate_id

def test_decisions_are_explicit_and_preserved(tmp_path: Path):
    engine=LearningEngine(tmp_path / "brain.db")
    candidate=engine.discover([obs(1),obs(2)])[0]
    assert engine.approve(candidate.candidate_id).decision == LearningDecision.APPROVED
    assert engine.discover([obs(1),obs(2),obs(3)])[0].decision == LearningDecision.APPROVED
