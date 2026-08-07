from pathlib import Path
import pytest
from app.brain.prediction.models import PredictionOutcome, PredictionStatus
from app.brain.prediction.service import PredictionEngine

def test_engine_create_and_resolve(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    p = engine.create(target="Supplier delay", prediction_type="delay", probability=.8, confidence=.9, horizon="7d")
    resolved = engine.resolve(p.prediction_id, PredictionOutcome.OCCURRED)
    assert resolved.status == PredictionStatus.RESOLVED
    assert resolved.outcome == PredictionOutcome.OCCURRED

def test_engine_rejects_double_resolution(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    p = engine.create(target="x", prediction_type="delay", probability=.8, confidence=.9, horizon="7d")
    engine.resolve(p.prediction_id, PredictionOutcome.OCCURRED)
    with pytest.raises(ValueError):
        engine.resolve(p.prediction_id, PredictionOutcome.DID_NOT_OCCUR)

def test_engine_expire(tmp_path: Path):
    engine = PredictionEngine(tmp_path / "b.db")
    p = engine.create(target="x", prediction_type="payment", probability=.7, confidence=.8, horizon="3d")
    assert engine.expire(p.prediction_id).status == PredictionStatus.EXPIRED
