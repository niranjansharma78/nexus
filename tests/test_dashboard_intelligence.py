from app.services.dashboard_intelligence_service import dashboard_intelligence

def test_dashboard_intelligence_shape():
    result = dashboard_intelligence()
    assert 'reviewed_24h' in result
    assert 'signals' in result
    assert isinstance(result['signals'], list)
