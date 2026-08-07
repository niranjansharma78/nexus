from pathlib import Path
from fastapi import APIRouter, Query
from app.brain.context_engine.service import ContextEngine

router = APIRouter(prefix="/api/v1/brain", tags=["context-engine"])

@router.get("/working-context")
def working_context(query: str = Query(..., min_length=1), world: str | None = None, max_items: int = 20):
    return ContextEngine(Path("data") / "nexus.db").build(query, world=world, max_items=max_items).to_dict()
