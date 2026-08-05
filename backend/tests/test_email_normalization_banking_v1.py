from app.services.email_normalizer import clean_email_text, safe_summary


def test_html_is_removed():
    value = "<!DOCTYPE html><html><body><p>₹12,500 credited</p></body></html>"
    cleaned = clean_email_text(value)
    assert "<html" not in cleaned.lower()
    assert "₹12,500 credited" in cleaned


def test_quoted_printable_is_decoded():
    cleaned = clean_email_text("Mark= et Digest =3D August")
    assert "Market Digest" in cleaned


def test_noisy_template_gets_fallback():
    summary = (
        "<html><style>font-family:Arial;mso-table-lspace:0;"
        "-webkit-text-size-adjust:none</style></html>"
    )
    cleaned = safe_summary("SBI Alert", summary, "finance")
    assert cleaned.startswith("SBI Alert")
