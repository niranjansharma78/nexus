from fastapi import APIRouter,Query
from app.services.executive_brief_service import executive_brief
router=APIRouter(prefix="/api/executive-brief")
@router.get("")
def get_brief(hours:int=Query(24,ge=1,le=168)):
    return executive_brief(hours)
