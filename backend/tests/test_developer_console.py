from app.services.developer_console_service import summary, evidence
def test_summary():
    s=summary()
    assert "totals" in s and "evidence" in s["totals"]
def test_limit():
    assert len(evidence(limit=5)) <= 5
