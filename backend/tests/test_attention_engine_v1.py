from pathlib import Path

from app.brain.attention.models import AttentionItem, AttentionPriority
from app.brain.attention.service import AttentionEngine


def make_item(**overrides):
    data = {
        "label": "Machine stopped",
        "importance": 0.9,
        "urgency": 0.9,
        "novelty": 0.7,
        "relevance": 0.9,
        "risk": 0.9,
        "confidence": 0.9,
    }
    data.update(overrides)
    return AttentionItem(**data)


def test_high_risk_item_becomes_critical_or_high():
    item = AttentionEngine().evaluate(make_item())
    assert item.priority in {
        AttentionPriority.CRITICAL,
        AttentionPriority.HIGH,
    }
    assert item.should_process_now is True
    assert item.should_escalate is True


def test_low_value_item_is_deferred():
    item = AttentionEngine().evaluate(
        make_item(
            importance=0.05,
            urgency=0.05,
            novelty=0.05,
            relevance=0.05,
            risk=0.05,
            confidence=0.05,
        )
    )
    assert item.priority == AttentionPriority.DEFER
    assert item.should_process_now is False


def test_rank_orders_highest_first():
    ranked = AttentionEngine().rank([
        make_item(label="Low", importance=0.2, urgency=0.2, risk=0.2),
        make_item(label="High"),
    ])
    assert ranked[0].label == "High"


def test_repository_round_trip(tmp_path: Path):
    engine = AttentionEngine(tmp_path / "brain.db")
    created = engine.evaluate(
        make_item(world="factory", source="mes")
    )
    loaded = engine.repository.list()
    assert len(loaded) == 1
    assert loaded[0].item_id == created.item_id
