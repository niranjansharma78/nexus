from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.brain.simulation.models import SimulationOption, SimulationOutcome
from app.brain.simulation.service import SimulationEngine

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])

class OutcomeRequest(BaseModel):
    label: str = Field(min_length=1)
    probability: float = Field(ge=0.0, le=1.0)
    value_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = ""

class OptionRequest(BaseModel):
    option_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    outcomes: list[OutcomeRequest] = []
    cost_score: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reversibility: float = Field(default=0.5, ge=0.0, le=1.0)
    constraint_violations: list[str] = []
    assumptions: list[str] = []

class SimulationRequest(BaseModel):
    objective: str = Field(min_length=1)
    current_state: dict[str, object]
    options: list[OptionRequest] = Field(min_length=1)
    horizon: str = Field(min_length=1)
    world: str | None = None
    constraints: list[str] = []
    assumptions: list[str] = []
    external_predictions: list[dict[str, object]] = []

def engine() -> SimulationEngine:
    return SimulationEngine(Path("data") / "nexus.db")

@router.post("/run")
def run_simulation(request: SimulationRequest):
    options = [SimulationOption(
        option_id=o.option_id,
        label=o.label,
        outcomes=[SimulationOutcome(**x.model_dump()) for x in o.outcomes],
        cost_score=o.cost_score,
        complexity_score=o.complexity_score,
        reversibility=o.reversibility,
        constraint_violations=o.constraint_violations,
        assumptions=o.assumptions,
    ) for o in request.options]
    return engine().create_and_run(
        objective=request.objective,
        current_state=request.current_state,
        options=options,
        horizon=request.horizon,
        world=request.world,
        constraints=request.constraints,
        assumptions=request.assumptions,
        external_predictions=request.external_predictions,
    ).to_dict()

@router.get("")
def list_simulations(limit: int = 100):
    return {"simulations": [item.to_dict() for item in engine().repository.list(limit=limit)]}

@router.get("/{simulation_id}")
def get_simulation(simulation_id: str):
    item = engine().repository.get(simulation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return item.to_dict()
