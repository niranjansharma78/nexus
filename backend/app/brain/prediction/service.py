from datetime import datetime, timezone
from pathlib import Path
from .calibration import CalibrationEngine
from .models import Prediction, PredictionOutcome, PredictionStatus
from .repository import PredictionRepository

class PredictionEngine:
    def __init__(self, database_path: str | Path) -> None:
        self.repository = PredictionRepository(database_path)
        self.calibration = CalibrationEngine()

    def create(self, **kwargs) -> Prediction:
        return self.repository.save(Prediction(**kwargs))

    def resolve(self, prediction_id: str, outcome: PredictionOutcome | str) -> Prediction:
        prediction = self.repository.get(prediction_id)
        if prediction is None:
            raise KeyError(f"Prediction not found: {prediction_id}")
        if prediction.status != PredictionStatus.OPEN:
            raise ValueError("Prediction is already closed")
        prediction.status = PredictionStatus.RESOLVED
        prediction.outcome = PredictionOutcome(outcome)
        prediction.resolved_at = datetime.now(timezone.utc).isoformat()
        return self.repository.save(prediction)

    def expire(self, prediction_id: str) -> Prediction:
        prediction = self.repository.get(prediction_id)
        if prediction is None:
            raise KeyError(f"Prediction not found: {prediction_id}")
        prediction.status = PredictionStatus.EXPIRED
        prediction.resolved_at = datetime.now(timezone.utc).isoformat()
        return self.repository.save(prediction)

    def calibration_summary(self, *, world: str | None = None,
                            prediction_type: str | None = None) -> dict[str, object]:
        predictions = self.repository.list(
            world=world, prediction_type=prediction_type, limit=500
        )
        return self.calibration.summarize(predictions).to_dict()
