from app.brain.simulation.models import Simulation, SimulationOption, SimulationOutcome
from app.brain.simulation.service import SimulationEngine


def make_option(option_id, value, risk, confidence=0.9, reversibility=0.5, violations=None):
    return SimulationOption(
        option_id=option_id,
        label=option_id,
        outcomes=[SimulationOutcome(label="Most likely", probability=1.0, value_score=value, risk_score=risk, confidence=confidence)],
        reversibility=reversibility,
        constraint_violations=violations or [],
    )


def test_engine_ranks_better_option_first():
    simulation = Simulation(objective="Choose", current_state={}, options=[make_option("weak", 0.4, 0.6), make_option("strong", 0.8, 0.2)], horizon="30d")
    result = SimulationEngine().run(simulation)
    assert result.recommended_option_id == "strong"


def test_constraint_violation_makes_option_infeasible():
    simulation = Simulation(objective="Choose", current_state={}, options=[make_option("blocked", 1.0, 0.0, violations=["No cash"]), make_option("feasible", 0.5, 0.5)], horizon="30d")
    result = SimulationEngine().run(simulation)
    blocked = next(x for x in result.ranking if x["option_id"] == "blocked")
    assert blocked["feasible"] is False
    assert result.recommended_option_id == "feasible"


def test_reversibility_contributes_to_score():
    simulation = Simulation(objective="Choose", current_state={}, options=[make_option("low", 0.6, 0.3, reversibility=0.0), make_option("high", 0.6, 0.3, reversibility=1.0)], horizon="7d")
    result = SimulationEngine().run(simulation)
    assert result.recommended_option_id == "high"


def test_external_predictions_are_optional():
    result = SimulationEngine().create_and_run(objective="Test", current_state={"cash": 100}, options=[make_option("a", 0.5, 0.2)], horizon="7d", external_predictions=[{"target": "cash", "probability": 0.8}])
    assert result.external_predictions[0]["probability"] == 0.8
