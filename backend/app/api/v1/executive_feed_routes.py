from fastapi import APIRouter, Query

from app.services.executive_feed_service import executive_feed


router = APIRouter(
    prefix="/api/v1/executive",
    tags=["executive"],
)


@router.get("/feed")
def get_feed(
    hours: int = Query(168, ge=1, le=2160),
    limit_per_section: int = Query(10, ge=1, le=50),
):
    return executive_feed(
        hours=hours,
        limit_per_section=limit_per_section,
    )
