from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.brain.runtime_v2.models import RuntimeTrigger
from app.brain.runtime_v2.service import CognitiveRuntimeV2


router = APIRouter(
    prefix="/api/v1/runtime-v2",
    tags=["runtime-v2"],
)


class RuntimeRequest(BaseModel):
    trigger: RuntimeTrigger = RuntimeTrigger.MANUAL
    objective: str = Field(min_length=1)
    world: str | None = None
    intent: str | None = None
    context_query: str | None = None
    prediction_inputs: list[dict[str, Any]] = []
    simulation_options: list[dict[str, Any]] = []
    decision_options: list[dict[str, Any]] = []
    plan_tasks: list[dict[str, Any]] = []
    constraints: list[str] = []
    metadata: dict[str, Any] = {}
    auto_execute_requested: bool = False


class EventRuntimeRequest(BaseModel):
    event: dict[str, Any]
    objective: str | None = None


def runtime() -> CognitiveRuntimeV2:
    return CognitiveRuntimeV2(Path("data") / "nexus.db")


@router.post("/run")
def run_runtime(request: RuntimeRequest):
    return runtime().run(**request.model_dump()).to_dict()


@router.post("/event")
def run_from_event(request: EventRuntimeRequest):
    return runtime().run_from_event(
        request.event,
        objective=request.objective,
    ).to_dict()
