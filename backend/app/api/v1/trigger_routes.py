from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.brain.triggers.models import TriggerKind
from app.brain.triggers.service import TriggerDispatcher


router = APIRouter(
    prefix="/api/v1/triggers",
    tags=["triggers"],
)


class TriggerRequest(BaseModel):
    kind: TriggerKind
    payload: dict[str, Any]
    world: str | None = None
    source: str | None = None
    objective: str | None = None
    metadata: dict[str, Any] = {}
    process_now: bool = True


def dispatcher() -> TriggerDispatcher:
    return TriggerDispatcher(Path("data") / "nexus.db")


@router.post("")
def submit_trigger(request: TriggerRequest):
    return dispatcher().submit(**request.model_dump()).to_dict()


@router.post("/process-pending")
def process_pending(limit: int = 100):
    return {
        "results": [
            item.to_dict()
            for item in dispatcher().process_pending(limit=limit)
        ]
    }
