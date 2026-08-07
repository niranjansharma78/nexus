from pathlib import Path
from app.brain.prediction.models import Prediction
from app.brain.prediction.repository import PredictionRepository

def test_repository_round_trip(tmp_path: Path):
    repo = PredictionRepository(tmp_path / "b.db")
    p = Prediction(target="Customer payment", prediction_type="payment", probability=.75, confidence=.9, horizon="5d", world="finance")
    repo.save(p)
    loaded = repo.get(p.prediction_id)
    assert loaded is not None
    assert loaded.world == "finance"

def test_repository_filters(tmp_path: Path):
    repo = PredictionRepository(tmp_path / "b.db")
    repo.save(Prediction(target="A", prediction_type="payment", probability=.7, confidence=.8, horizon="5d", world="finance"))
    repo.save(Prediction(target="B", prediction_type="delay", probability=.6, confidence=.7, horizon="1d", world="factory"))
    assert len(repo.list(world="finance")) == 1
    assert len(repo.list(prediction_type="delay")) == 1
