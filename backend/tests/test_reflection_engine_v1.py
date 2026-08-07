from pathlib import Path

from app.brain.reflection.service import ReflectionEngine


def test_reflection_confidence_delta():
    record = ReflectionEngine().reflect(
        subject="Supplier delay",
        expected="Delay likely",
        actual="Delay occurred",
        lesson="Recent supplier history was useful.",
        confidence_before=0.7,
        confidence_after=0.85,
    )

    assert record.confidence_delta == 0.15


def test_alignment_detects_followed_recommendation():
    engine = ReflectionEngine()
    record = engine.reflect(
        subject="Supplier strategy",
        expected="Replace supplier",
        actual="Supplier replaced",
        lesson="Replacement reduced delay.",
        confidence_before=0.7,
        confidence_after=0.9,
        chosen_option_id="replace",
        recommended_option_id="replace",
    )

    result = engine.outcome_alignment(record)

    assert result["recommendation_followed"] is True


def test_repository_round_trip(tmp_path: Path):
    engine = ReflectionEngine(tmp_path / "brain.db")

    created = engine.reflect(
        subject="Customer payment",
        expected="Payment this week",
        actual="Paid two days late",
        lesson="Customer tends to slip slightly.",
        confidence_before=0.8,
        confidence_after=0.75,
        world="finance",
    )

    loaded = engine.repository.get(created.reflection_id)

    assert loaded is not None
    assert loaded.subject == "Customer payment"


def test_assumption_failures_are_preserved():
    record = ReflectionEngine().reflect(
        subject="Production plan",
        expected="Target achieved",
        actual="Target missed",
        lesson="Maintenance assumption failed.",
        confidence_before=0.85,
        confidence_after=0.6,
        assumption_failures=["Machine availability"],
    )

    assert record.assumption_failures == ["Machine availability"]
