from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.brain.reflection.service import ReflectionEngine


router = APIRouter(
    prefix="/api/v1/reflection",
    tags=["reflection"],
)


class ReflectionRequest(BaseModel):
    subject: str = Field(min_length=1)
    expected: str
    actual: str
    lesson: str = Field(min_length=1)
    confidence_before: float = Field(ge=0.0, le=1.0)
    confidence_after: float = Field(ge=0.0, le=1.0)
    world: str | None = None
    prediction_id: str | None = None
    simulation_id: str | None = None
    chosen_option_id: str | None = None
    recommended_option_id: str | None = None
    assumption_failures: list[str] = []
    evidence_ids: list[int] = []


def engine() -> ReflectionEngine:
    return ReflectionEngine(Path("data") / "nexus.db")


@router.post("")
def create_reflection(request: ReflectionRequest):
    return engine().reflect(**request.model_dump()).to_dict()


@router.get("")
def list_reflections(limit: int = 100):
    return {
        "reflections": [
            item.to_dict()
            for item in engine().repository.list(limit=limit)
        ]
    }


@router.get("/{reflection_id}")
def get_reflection(reflection_id: str):
    item = engine().repository.get(reflection_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return item.to_dict()
