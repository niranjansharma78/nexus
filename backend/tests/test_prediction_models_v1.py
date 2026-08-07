import pytest
from app.brain.prediction.models import Prediction

def test_prediction_validates_probability():
    with pytest.raises(ValueError):
        Prediction(target="x", prediction_type="risk", probability=1.1, confidence=.8, horizon="1d")

def test_prediction_validates_confidence():
    with pytest.raises(ValueError):
        Prediction(target="x", prediction_type="risk", probability=.7, confidence=-.1, horizon="1d")

def test_prediction_serialization():
    p = Prediction(target="x", prediction_type="risk", probability=.7, confidence=.8, horizon="1d")
    d = p.to_dict()
    assert d["status"] == "open"
    assert d["outcome"] is None
