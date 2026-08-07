from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.brain.prediction.models import PredictionOutcome, PredictionStatus
from app.brain.prediction.service import PredictionEngine

router = APIRouter(prefix="/api/v1/brain", tags=["prediction"])

def engine() -> PredictionEngine:
    return PredictionEngine(Path("data") / "nexus.db")

class PredictionCreateRequest(BaseModel):
    target: str = Field(min_length=1)
    prediction_type: str = Field(min_length=1)
    probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    horizon: str = Field(min_length=1)
    expected_by: str | None = None
    rationale: str = ""
    assumptions: list[str] = []
    evidence_ids: list[int] = []
    related_event_ids: list[str] = []
    world: str | None = None

class PredictionResolveRequest(BaseModel):
    outcome: PredictionOutcome

@router.post("/predictions")
def create_prediction(request: PredictionCreateRequest):
    return engine().create(**request.model_dump()).to_dict()

@router.get("/predictions")
def list_predictions(status: PredictionStatus | None = None, world: str | None = None,
                     prediction_type: str | None = None, limit: int = 100):
    return {"predictions": [
        item.to_dict() for item in engine().repository.list(
            status=status, world=world, prediction_type=prediction_type, limit=limit
        )
    ]}

@router.post("/predictions/{prediction_id}/resolve")
def resolve_prediction(prediction_id: str, request: PredictionResolveRequest):
    try:
        return engine().resolve(prediction_id, request.outcome).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@router.get("/calibration")
def calibration(world: str | None = None, prediction_type: str | None = None):
    return engine().calibration_summary(world=world, prediction_type=prediction_type)
