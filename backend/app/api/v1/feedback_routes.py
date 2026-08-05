from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.intelligence_feedback_service import (
    feedback_summary,
    record_feedback,
)


router = APIRouter(
    prefix="/api/v1/intelligence-feedback",
    tags=["intelligence-feedback"],
)


class FeedbackRequest(BaseModel):
    feedback_type: str
    evidence_id: int | None = None
    business_event_id: int | None = None
    original_value: str | None = None
    corrected_value: str | None = None
    note: str | None = None


@router.post("")
def submit_feedback(payload: FeedbackRequest):
    try:
        return record_feedback(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/summary")
def get_feedback_summary():
    return feedback_summary()
