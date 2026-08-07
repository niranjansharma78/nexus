from pathlib import Path
from fastapi import APIRouter
from app.brain.core.context import BrainContextBuilder
from app.brain.executive_reasoning.service import ExecutiveReasoningEngine
router=APIRouter(prefix="/api/v1/brain",tags=["executive-reasoning"])
@router.get("/executive-brief")
def executive_brief(limit:int=10):
    context=BrainContextBuilder(Path("data")/"nexus.db").build()
    return ExecutiveReasoningEngine().executive_brief(context,limit=limit)
