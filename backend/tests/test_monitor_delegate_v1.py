from app.services.delegation_service import (
    create_delegation,
    ensure_delegation_schema,
    set_monitor_status,
)


def test_monitor_can_be_acknowledged():
    ensure_delegation_schema()
    row = set_monitor_status(
        evidence_id=888881,
        status="acknowledged",
    )
    assert row["status"] == "acknowledged"


def test_monitor_can_be_delegated():
    row = create_delegation(
        evidence_id=888882,
        title="Production confirmed",
        summary="Planning should schedule the next step.",
        owner="Planning",
    )
    assert row["owner"] == "Planning"
    assert row["status"] == "open"
