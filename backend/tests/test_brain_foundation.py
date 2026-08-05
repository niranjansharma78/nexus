from app.brain.priority_engine import score_evidence
from app.brain.relationship_engine import build_relationship_snapshots
from app.services.brain_service import brain_state

def test_priority():
    result=score_evidence({
        "signal_score":60,"category":"finance","title":"Urgent payment overdue",
        "summary":"Action required today","domain":"business",
        "relationship_impact":"negative","confidence":0.9,"requires_decision":0
    })
    assert result["score"]>=80
    assert result["requires_decision"] is True

def test_relationship_decline():
    rows=[
        {"entity_name":"ABC","relationship_impact":"negative","occurred_at":"2026-08-01"},
        {"entity_name":"ABC","relationship_impact":"negative","occurred_at":"2026-08-02"},
        {"entity_name":"ABC","relationship_impact":"neutral","occurred_at":"2026-08-03"},
    ]
    assert build_relationship_snapshots(rows)[0]["direction"]=="declining"

def test_brain_shape():
    state=brain_state()
    assert "brain" in state and "morning_brief" in state
