from app.services.banking_highlights_service import (
    _bank_name,
    _compact_label,
    _counterparty,
)


def test_bank_name_from_sender():
    assert _bank_name("alert from neft@idbi.co.in") == "IDBI Bank"


def test_notification_sender_not_used_as_counterparty():
    assert _counterparty(
        "₹2,00,000 credited from neft@idbi.co.in",
        "credit",
        None,
    ) is None


def test_credit_label():
    assert _compact_label(
        direction="credit",
        bank="IDBI Bank",
        counterparty="ABC Ltd",
    ) == "Credit · IDBI Bank · ABC Ltd"


def test_debit_label_without_counterparty():
    assert _compact_label(
        direction="debit",
        bank="SBI",
        counterparty=None,
    ) == "Debit · SBI"


def test_cheque_bounce_label():
    assert _compact_label(
        direction="cheque_bounce",
        bank="HDFC Bank",
        counterparty="Customer X",
    ) == "Cheque Bounce · HDFC Bank · Customer X"
