from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.brain_service import brain_state, refresh_brain
from app.brain.memory_engine import remember

router = APIRouter(prefix="/api/brain")

class MemoryCreate(BaseModel):
    memory_type: str
    title: str
    content: str
    entity_name: str | None = None
    importance: int = Field(default=50, ge=0, le=100)
    confidence: float = Field(default=0.75, ge=0, le=1)

@router.get("/state")
def get_state():
    return brain_state()

@router.post("/refresh")
def refresh():
    return refresh_brain()

@router.post("/memory")
def create_memory(payload: MemoryCreate):
    return {"ok":True,"memory_id":remember(
        payload.memory_type,payload.title,payload.content,payload.entity_name,payload.importance,payload.confidence
    )}
