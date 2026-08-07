from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.brain.decision.models import DecisionOption
from app.brain.decision.service import DecisionEngine


router = APIRouter(
    prefix="/api/v1/decision",
    tags=["decision"],
)


class OptionRequest(BaseModel):
    option_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    expected_value: float = Field(ge=0.0, le=1.0)
    expected_risk: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reversibility: float = Field(default=0.5, ge=0.0, le=1.0)
    cost_score: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    constraint_violations: list[str] = []
    rationale: str = ""


class DecisionRequest(BaseModel):
    objective: str = Field(min_length=1)
    options: list[OptionRequest] = Field(min_length=1)
    world: str | None = None
    intent: str | None = None
    context_summary: dict[str, object] = {}
    prediction_refs: list[str] = []
    simulation_refs: list[str] = []
    constraints: list[str] = []


class ChoiceRequest(BaseModel):
    option_id: str = Field(min_length=1)
    approve: bool = True


def engine() -> DecisionEngine:
    return DecisionEngine(Path("data") / "nexus.db")


@router.post("/evaluate")
def evaluate(request: DecisionRequest):
    options = [
        DecisionOption(**item.model_dump())
        for item in request.options
    ]

    return engine().decide(
        objective=request.objective,
        options=options,
        world=request.world,
        intent=request.intent,
        context_summary=request.context_summary,
        prediction_refs=request.prediction_refs,
        simulation_refs=request.simulation_refs,
        constraints=request.constraints,
    ).to_dict()


@router.post("/{decision_id}/choose")
def choose(decision_id: str, request: ChoiceRequest):
    try:
        return engine().choose(
            decision_id,
            request.option_id,
            approve=request.approve,
        ).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("")
def list_decisions(limit: int = 100):
    return {
        "decisions": [
            item.to_dict()
            for item in engine().repository.list(limit=limit)
        ]
    }


@router.get("/{decision_id}")
def get_decision(decision_id: str):
    item = engine().repository.get(decision_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return item.to_dict()
