from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.brain.attention.models import AttentionItem
from app.brain.attention.service import AttentionEngine


router = APIRouter(
    prefix="/api/v1/attention",
    tags=["attention"],
)


class AttentionRequest(BaseModel):
    label: str = Field(min_length=1)
    importance: float = Field(ge=0.0, le=1.0)
    urgency: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    risk: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    world: str | None = None
    source: str | None = None
    reference_id: str | None = None


def engine() -> AttentionEngine:
    return AttentionEngine(Path("data") / "nexus.db")


@router.post("/evaluate")
def evaluate(request: AttentionRequest):
    return engine().evaluate(
        AttentionItem(**request.model_dump())
    ).to_dict()


@router.get("")
def list_attention(limit: int = 100):
    return {
        "items": [
            item.to_dict()
            for item in engine().repository.list(limit=limit)
        ]
    }
