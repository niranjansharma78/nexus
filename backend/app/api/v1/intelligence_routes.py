from fastapi import APIRouter
from pydantic import BaseModel

from app.services.event_intelligence_service import extract_business_events


router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


class InterpretRequest(BaseModel):
    title: str
    summary: str = ""
    entity_name: str | None = None


@router.post("/interpret")
def interpret(payload: InterpretRequest):
    events = extract_business_events(
        title=payload.title,
        summary=payload.summary,
        entity_name=payload.entity_name,
    )

    return {
        "event_count": len(events),
        "events": events,
    }
