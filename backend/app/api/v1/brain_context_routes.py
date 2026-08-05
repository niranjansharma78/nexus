from pathlib import Path

from fastapi import APIRouter

from app.brain.core.context import BrainContextBuilder


router = APIRouter(prefix="/api/v1/brain", tags=["brain-core"])


@router.get("/context")
def get_brain_context():
    builder = BrainContextBuilder(Path("data") / "nexus.db")
    context = builder.build()

    return {
        "events": context.events,
        "learnings": context.learnings,
        "open_questions": context.open_questions,
        "journal_entries": context.journal_entries,
        "timeline": [
            {
                "occurred_at": item.occurred_at,
                "kind": item.kind,
                "label": item.label,
                "reference_id": item.reference_id,
            }
            for item in context.timeline
        ],
        "confidence": context.confidence,
        "confidence_band": context.confidence_band,
        "summary": context.summary,
    }
