from pathlib import Path

from app.brain.decision.models import DecisionOption, DecisionStatus
from app.brain.decision.service import DecisionEngine


def option(
    option_id: str,
    *,
    value: float,
    risk: float,
    confidence: float = 0.9,
    reversibility: float = 0.5,
    violations=None,
):
    return DecisionOption(
        option_id=option_id,
        label=option_id,
        expected_value=value,
        expected_risk=risk,
        confidence=confidence,
        reversibility=reversibility,
        constraint_violations=violations or [],
    )


def test_decision_ranks_best_feasible_option():
    result = DecisionEngine().decide(
        objective="Choose supplier",
        options=[
            option("wait", value=0.5, risk=0.5),
            option("replace", value=0.9, risk=0.2),
        ],
    )

    assert result.recommended_option_id == "replace"


def test_constraint_violation_blocks_option():
    result = DecisionEngine().decide(
        objective="Choose",
        options=[
            option(
                "blocked",
                value=1.0,
                risk=0.0,
                violations=["No cash"],
            ),
            option("safe", value=0.5, risk=0.5),
        ],
    )

    assert result.recommended_option_id == "safe"


def test_decision_persists_and_choice_updates(tmp_path: Path):
    engine = DecisionEngine(tmp_path / "brain.db")

    created = engine.decide(
        objective="Supplier decision",
        options=[
            option("wait", value=0.5, risk=0.5),
            option("replace", value=0.9, risk=0.2),
        ],
        world="factory",
        intent="reduce delay",
    )

    chosen = engine.choose(created.decision_id, "replace")

    assert chosen.status == DecisionStatus.APPROVED
    assert chosen.chosen_option_id == "replace"
    assert chosen.resolved_at is not None


def test_unknown_choice_is_rejected(tmp_path: Path):
    engine = DecisionEngine(tmp_path / "brain.db")
    created = engine.decide(
        objective="Test",
        options=[option("a", value=0.5, risk=0.2)],
    )

    try:
        engine.choose(created.decision_id, "missing")
        assert False, "Expected ValueError"
    except ValueError:
        pass
