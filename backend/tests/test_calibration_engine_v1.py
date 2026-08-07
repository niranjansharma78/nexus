from pathlib import Path
from app.brain.prediction.models import PredictionOutcome
from app.brain.prediction.service import PredictionEngine

def resolved_prediction(engine, probability, occurred):
    p = engine.create(target=f"{probability}-{occurred}", prediction_type="test", probability=probability, confidence=.9, horizon="1d")
    return engine.resolve(p.prediction_id, PredictionOutcome.OCCURRED if occurred else PredictionOutcome.DID_NOT_OCCUR)

def test_calibration_empty(tmp_path: Path):
    assert PredictionEngine(tmp_path / "b.db").calibration_summary()["bias"] == "insufficient_data"

def test_brier_score_and_well_calibrated(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    resolved_prediction(engine, .8, True)
    resolved_prediction(engine, .2, False)
    summary = engine.calibration_summary()
    assert summary["brier_score"] == .04
    assert summary["bias"] == "well_calibrated"

def test_overconfidence_detection(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    resolved_prediction(engine, .9, False)
    resolved_prediction(engine, .9, True)
    assert engine.calibration_summary()["bias"] == "overconfident"

def test_underconfidence_detection(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    resolved_prediction(engine, .3, True)
    resolved_prediction(engine, .3, True)
    assert engine.calibration_summary()["bias"] == "underconfident"
