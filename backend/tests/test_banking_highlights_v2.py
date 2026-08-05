from app.services.banking_highlights_service import _amount,_compact_summary,_direction,_is_promotional

def test_amazon_voucher_is_promotional():
    assert _is_promotional("Claim your Amazon voucher today") is True

def test_credit_summary_is_compact():
    assert _compact_summary("credit",250000,"ABC Ltd","") == "₹250,000 credited from ABC Ltd"

def test_debit_summary_is_compact():
    assert _compact_summary("debit",78400,"Vendor XYZ","") == "₹78,400 debited to Vendor XYZ"

def test_cheque_bounce_is_highlight_type():
    assert _direction("Cheque returned unpaid. Payment dishonoured.") == "cheque_bounce"

def test_amount_detection():
    assert _amount("INR 2,50,000 credited") == 250000.0
