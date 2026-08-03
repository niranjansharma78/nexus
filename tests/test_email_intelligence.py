from app.services.email_intelligence import interpret_email

def test_claron_invoice_is_business_finance():
    r = interpret_email(subject="Invoice No.172 1F FTTH dated 31.07.2026 - Claron", body="Please find attached invoice for 1F FTTH.", sender="backoffice@claronfibreoptics.com")
    assert r.domain == "business"
    assert r.category == "finance"
    assert r.signal_score >= 60

def test_school_mail_is_family():
    r = interpret_email(subject="Parent teacher meeting tomorrow", body="Please attend the school meeting.", sender="school@example.com")
    assert r.domain == "family"

def test_newsletter_is_low_signal():
    r = interpret_email(subject="Newsletter July 2026", body="View in browser. Unsubscribe. Special offer.", sender="marketing@example.com")
    assert r.category == "promotion"
    assert r.signal_score <= 20

def test_urgent_dispatch_needs_decision():
    r = interpret_email(subject="Urgent dispatch delayed", body="Action required. Customer dispatch is delayed.", sender="accounts@claronfibreoptics.com")
    assert r.requires_decision == 1
    assert r.priority == 1
