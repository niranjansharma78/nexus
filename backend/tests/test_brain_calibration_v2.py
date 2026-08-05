from app.brain.decision_engine import classify_attention, normalize_category


def test_recruitment_overrides_generic_category():
    assert normalize_category({
        "title": "WorkIndia candidate ready for Sales Manager interview",
        "summary": "Candidate alert",
        "category": "communication",
    }) == "recruitment"


def test_information_is_not_signal():
    result = classify_attention({
        "title": "Dispatch Details",
        "summary": "Shipment dispatched.",
        "category": "procurement",
        "signal_score": 80,
        "brain_priority": 92,
    })
    assert result["attention_type"] == "information"
    assert result["requires_decision"] is False


def test_followup_is_separate_from_decision():
    result = classify_attention({
        "title": "Payment pending",
        "summary": "Please update the status.",
        "category": "finance",
        "signal_score": 60,
        "brain_priority": 72,
    })
    assert result["attention_type"] == "follow_up"
    assert result["requires_decision"] is False
    assert result["requires_followup"] is True
