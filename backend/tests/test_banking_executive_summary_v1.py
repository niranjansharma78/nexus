from app.services.banking_highlights_service import (
    _amount,
    _bank_name,
    _counterparty,
    _direction,
    _is_promotional,
)


def test_amount_detection():
    assert _amount("INR 2,50,000 credited") == 250000.0


def test_bank_detection_from_sender():
    assert _bank_name(
        "account credited",
        "NEFT Alerts <neft@idbi.co.in>",
        None,
    ) == "IDBI Bank"


def test_promotional_voucher_is_ignored():
    assert _is_promotional(
        "Claim your Amazon gift voucher today"
    ) is True


def test_cheque_bounce_detection():
    assert _direction(
        "Cheque returned unpaid"
    ) == "cheque_bounce"


def test_real_counterparty_detection():
    assert _counterparty(
        "INR 2,00,000 credited from ABC INDUSTRIES on 04-Aug",
        "credit",
        None,
    ) == "ABC INDUSTRIES"
