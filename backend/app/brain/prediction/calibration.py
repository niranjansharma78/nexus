from __future__ import annotations
from dataclasses import dataclass
from .models import Prediction, PredictionOutcome

@dataclass(slots=True, frozen=True)
class CalibrationSummary:
    resolved_count: int
    brier_score: float
    mean_probability: float
    actual_rate: float
    calibration_gap: float
    bias: str

    def to_dict(self) -> dict[str, object]:
        return {
            "resolved_count": self.resolved_count,
            "brier_score": self.brier_score,
            "mean_probability": self.mean_probability,
            "actual_rate": self.actual_rate,
            "calibration_gap": self.calibration_gap,
            "bias": self.bias,
        }

class CalibrationEngine:
    def summarize(self, predictions: list[Prediction]) -> CalibrationSummary:
        usable = [
            p for p in predictions
            if p.status.value == "resolved"
            and p.outcome in {PredictionOutcome.OCCURRED, PredictionOutcome.DID_NOT_OCCUR}
        ]
        if not usable:
            return CalibrationSummary(0, 0.0, 0.0, 0.0, 0.0, "insufficient_data")

        outcomes = [1.0 if p.outcome == PredictionOutcome.OCCURRED else 0.0 for p in usable]
        probabilities = [float(p.probability) for p in usable]
        brier = sum((p - o) ** 2 for p, o in zip(probabilities, outcomes)) / len(usable)
        mean_probability = sum(probabilities) / len(probabilities)
        actual_rate = sum(outcomes) / len(outcomes)
        gap = mean_probability - actual_rate

        if gap > 0.10:
            bias = "overconfident"
        elif gap < -0.10:
            bias = "underconfident"
        else:
            bias = "well_calibrated"

        return CalibrationSummary(
            len(usable),
            round(brier, 10),
            round(mean_probability, 10),
            round(actual_rate, 10),
            round(gap, 10),
            bias,
        )
