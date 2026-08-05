from app.services.executive_feed_service import executive_feed


def test_executive_feed_has_required_sections():
    result = executive_feed(hours=2160)

    assert "alerts" in result
    assert "notices" in result
    assert "delegations" in result
    assert "monitoring" in result
    assert "summary" in result
