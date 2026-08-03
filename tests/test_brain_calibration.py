from app.brain.decision_engine import classify_attention, normalize_category


def test_confirmation_is_not_decision():
    result = classify_attention({
        "title": "Production Confirmation | Claron",
        "summary": "Production confirmed for August.",
        "category": "operations",
        "signal_score": 60,
        "brain_priority": 72,
    })
    assert result["attention_type"] == "information"
    assert result["requires_decision"] is False


def test_explicit_action_becomes_decision():
    result = classify_attention({
        "title": "Urgent payment approval required",
        "summary": "Please approve this payment today.",
        "category": "finance",
        "signal_score": 80,
        "brain_priority": 92,
    })
    assert result["attention_type"] == "decision"
    assert result["requires_decision"] is True


def test_recruitment_is_grouped():
    result = classify_attention({
        "title": "Candidate ready for Sales Manager interview",
        "summary": "WorkIndia candidate alert.",
        "category": None,
        "signal_score": 60,
        "brain_priority": 60,
    })
    assert result["attention_type"] == "grouped"
    assert result["requires_decision"] is False


def test_missing_category_is_inferred():
    assert normalize_category({
        "title": "Re: Production Confirmation",
        "summary": "Production status confirmed.",
        "category": None,
    }) == "operations"
