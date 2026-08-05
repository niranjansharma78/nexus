from fastapi import APIRouter, Query

from app.services.conversation_engine_service import (
    correlate_unlinked_events,
    list_conversations,
)


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["conversations"],
)


@router.post("/correlate")
def correlate(
    limit: int = Query(500, ge=1, le=5000),
):
    return correlate_unlinked_events(limit=limit)


@router.get("")
def get_conversations(
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    return {
        "items": list_conversations(
            status=status,
            limit=limit,
        )
    }
