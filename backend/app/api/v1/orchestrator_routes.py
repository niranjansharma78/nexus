from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.brain.orchestrator.models import OrchestrationRequest
from app.brain.orchestrator.service import CognitiveOrchestrator


router = APIRouter(
    prefix="/api/v1/orchestrator",
    tags=["orchestrator"],
)


class OrchestrateRequest(BaseModel):
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


@router.post("/run")
def run_orchestration(request: OrchestrateRequest):
    payload = OrchestrationRequest(**request.model_dump())
    return CognitiveOrchestrator(
        Path("data") / "nexus.db"
    ).run(payload).to_dict()
