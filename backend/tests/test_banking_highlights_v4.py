from app.services.banking_highlights_service import (
    _bank_name,
    _counterparty,
)


def test_bank_detected_from_sender_domain():
    assert _bank_name(
        "account credited",
        "NEFT Alerts <neft@idbi.co.in>",
        None,
    ) == "IDBI Bank"


def test_bank_detected_from_hdfc_sender():
    assert _bank_name(
        "transaction alert",
        "alerts@hdfcbank.net",
        None,
    ) == "HDFC Bank"


def test_notification_sender_not_used_as_source():
    assert _counterparty(
        "₹2,00,000 credited from neft@idbi.co.in",
        "credit",
        None,
    ) is None


def test_real_source_is_detected():
    assert _counterparty(
        "INR 2,00,000 credited from ABC INDUSTRIES on 04-Aug",
        "credit",
        None,
    ) == "ABC INDUSTRIES"
