from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.brain.planning.models import PlanTask, TaskStatus
from app.brain.planning.service import PlanningEngine


router = APIRouter(
    prefix="/api/v1/planning",
    tags=["planning"],
)


class TaskRequest(BaseModel):
    title: str = Field(min_length=1)
    owner: str | None = None
    due_at: str | None = None
    duration_hours: float = Field(default=1.0, ge=0.0)
    dependencies: list[str] = []
    priority: float = Field(default=0.5, ge=0.0, le=1.0)
    task_id: str | None = None


class PlanRequest(BaseModel):
    objective: str = Field(min_length=1)
    tasks: list[TaskRequest] = Field(min_length=1)
    world: str | None = None
    decision_refs: list[str] = []
    simulation_refs: list[str] = []
    constraints: list[str] = []


class TaskUpdateRequest(BaseModel):
    status: TaskStatus | None = None
    progress: float | None = Field(default=None, ge=0.0, le=1.0)


def engine() -> PlanningEngine:
    return PlanningEngine(Path("data") / "nexus.db")


@router.post("")
def create_plan(request: PlanRequest):
    tasks = []
    for item in request.tasks:
        payload = item.model_dump()
        task_id = payload.pop("task_id")
        tasks.append(
            PlanTask(
                **payload,
                **({"task_id": task_id} if task_id else {}),
            )
        )

    try:
        return engine().create_plan(
            objective=request.objective,
            tasks=tasks,
            world=request.world,
            decision_refs=request.decision_refs,
            simulation_refs=request.simulation_refs,
            constraints=request.constraints,
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{plan_id}/tasks/{task_id}")
def update_task(
    plan_id: str,
    task_id: str,
    request: TaskUpdateRequest,
):
    try:
        return engine().update_task(
            plan_id,
            task_id,
            status=request.status,
            progress=request.progress,
        ).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("")
def list_plans(limit: int = 100):
    return {
        "plans": [
            item.to_dict()
            for item in engine().repository.list(limit=limit)
        ]
    }


@router.get("/{plan_id}")
def get_plan(plan_id: str):
    item = engine().repository.get(plan_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return item.to_dict()
