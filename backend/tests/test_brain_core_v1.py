from pathlib import Path

from app.brain.core.confidence import ConfidenceService
from app.brain.core.context import BrainContextBuilder
from app.brain.core.evidence import EvidenceRef
from app.brain.core.timeline import TimelineItem
from app.brain.curiosity.models import CuriosityQuestion
from app.brain.curiosity.repository import CuriosityRepository
from app.brain.journal.models import BrainJournalEntry
from app.brain.journal.repository import BrainJournalRepository
from app.brain.learning.models import LearningCandidate, LearningDecision
from app.brain.learning.repository import LearningRepository
from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)


def test_confidence_service():
    assert ConfidenceService.normalize(1.2) == 1.0
    assert ConfidenceService.combine([0.5, 0.5]) == 0.75
    assert ConfidenceService.average([0.6, 0.8]) == 0.7
    assert ConfidenceService.band(0.9) == "high"
    assert ConfidenceService.band(0.7) == "likely"
    assert ConfidenceService.band(0.4) == "review"


def test_evidence_and_timeline_validate():
    evidence = EvidenceRef(evidence_id=1, source="email", confidence=0.9)
    assert evidence.source == "email"

    item = TimelineItem(
        occurred_at="2026-08-05T10:00:00+00:00",
        kind="event",
        label="Observed event",
    )
    assert item.kind == "event"


def test_context_builder_assembles_shared_brain_context(tmp_path: Path):
    db = tmp_path / "brain.db"

    UniversalEventRepository(db).save(
        UniversalEvent(
            event_id="event-1",
            object=UniversalObjectRef(kind="event", label="Event 1"),
            intent="observation",
            transition=UniversalTransition.OBSERVED,
            state="observed",
            world="business",
            confidence=0.8,
            source="test",
        )
    )

    LearningRepository(db).save(
        LearningCandidate(
            candidate_id="learning-1",
            source_label="A",
            target_label="B",
            relation="related_to",
            evidence_count=2,
            confidence=0.9,
            first_seen="2026-08-05T09:00:00+00:00",
            last_seen="2026-08-05T10:00:00+00:00",
            decision=LearningDecision.APPROVED,
        )
    )

    CuriosityRepository(db).save(
        CuriosityQuestion(
            question_id="question-1",
            question="What is this?",
            reason="Unknown meaning",
            priority=70,
            confidence=0.4,
        )
    )

    BrainJournalRepository(db).save(
        BrainJournalEntry(
            journal_date="2026-08-05",
            scope="organization",
            summary="Daily summary",
        )
    )

    context = BrainContextBuilder(db).build()

    assert context.summary["event_count"] == 1
    assert context.summary["approved_learning_count"] == 1
    assert context.summary["open_question_count"] == 1
    assert context.summary["journal_entry_count"] == 1
    assert len(context.timeline) == 1
    assert context.confidence == 0.85
    assert context.confidence_band == "high"


def test_context_excludes_unapproved_learning(tmp_path: Path):
    db = tmp_path / "brain.db"

    LearningRepository(db).save(
        LearningCandidate(
            candidate_id="learning-1",
            source_label="A",
            target_label="B",
            relation="related_to",
            evidence_count=2,
            confidence=0.9,
            first_seen="2026-08-05T09:00:00+00:00",
            last_seen="2026-08-05T10:00:00+00:00",
            decision=LearningDecision.PENDING,
        )
    )

    context = BrainContextBuilder(db).build()

    assert context.learnings == []
    assert context.summary["approved_learning_count"] == 0
