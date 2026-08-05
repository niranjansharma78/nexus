from app.services.event_intelligence_service import extract_business_events


def test_cheque_bounce_is_alert():
    events = extract_business_events(
        title="Cheque Bounce",
        summary="Payment instrument returned unpaid.",
        entity_name="Customer ABC",
    )
    assert any(
        event["event_type"] == "cheque_bounce"
        and event["visibility"] == "alert"
        for event in events
    )


def test_production_confirmation_is_notice_and_delegate():
    events = extract_business_events(
        title="Production Confirmation | Excell Telesonic",
        summary="Purchase order PO-4587 received. Production confirmed.",
        entity_name="Excell Telesonic",
    )

    event_types = {event["event_type"] for event in events}
    assert "purchase_order_received" in event_types
    assert "production_confirmed" in event_types
    assert "planning_delegation_suggested" in event_types


def test_dispatch_creates_notice_and_closure_watch():
    events = extract_business_events(
        title="Dispatch Details",
        summary="Material dispatched through transporter.",
        entity_name="Excell Telesonic",
    )

    event_types = {event["event_type"] for event in events}
    assert "dispatch_details_received" in event_types
    assert "delivery_confirmation_expected" in event_types
