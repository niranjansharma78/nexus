from pathlib import Path
from app.brain.simulation.models import SimulationOption, SimulationOutcome
from app.brain.simulation.service import SimulationEngine


def test_repository_round_trip(tmp_path: Path):
    engine = SimulationEngine(tmp_path / "brain.db")
    created = engine.create_and_run(
        objective="Supplier decision",
        current_state={"supplier": "ABC"},
        options=[SimulationOption(option_id="wait", label="Wait", outcomes=[SimulationOutcome(label="Delivery improves", probability=0.6, value_score=0.6, risk_score=0.4, confidence=0.7)])],
        horizon="14d",
        world="factory",
    )
    loaded = engine.repository.get(created.simulation_id)
    assert loaded is not None
    assert loaded.objective == "Supplier decision"
    assert loaded.recommended_option_id == "wait"
