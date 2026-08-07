import pytest
from app.brain.simulation.models import Simulation, SimulationOption, SimulationOutcome


def test_outcome_validates_probability():
    with pytest.raises(ValueError):
        SimulationOutcome(label="Invalid", probability=1.1, value_score=0.5, risk_score=0.5, confidence=0.5)


def test_simulation_requires_option():
    with pytest.raises(ValueError):
        Simulation(objective="Test", current_state={}, options=[], horizon="7d")


def test_option_serializes_outcomes():
    option = SimulationOption(option_id="a", label="Option A", outcomes=[SimulationOutcome(label="Success", probability=0.7, value_score=0.8, risk_score=0.2, confidence=0.9)])
    assert option.to_dict()["outcomes"][0]["label"] == "Success"
