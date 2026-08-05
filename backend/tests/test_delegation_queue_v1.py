from app.services.delegation_service import (
    create_delegation,
    ensure_delegation_schema,
    list_delegations,
    set_monitor_status,
)


def test_delegation_schema_and_create():
    ensure_delegation_schema()
    row = create_delegation(
        evidence_id=None,
        title="Test delegation",
        summary="Assign this internally.",
        owner="Planning",
    )
    assert row["owner"] == "Planning"
    assert row["status"] == "open"


def test_list_delegations():
    rows = list_delegations()
    assert isinstance(rows, list)


def test_monitor_acknowledgement():
    row = set_monitor_status(
        evidence_id=999999,
        status="acknowledged",
    )
    assert row["status"] == "acknowledged"
