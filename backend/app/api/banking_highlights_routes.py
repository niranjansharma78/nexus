from fastapi import APIRouter, Query

from app.services.banking_highlights_service import banking_highlights

router = APIRouter(prefix="/api/banking-highlights")


@router.get("")
def get_banking_highlights(
    hours: int = Query(72, ge=1, le=720),
    limit: int = Query(8, ge=1, le=30),
):
    return banking_highlights(hours=hours, limit=limit)
