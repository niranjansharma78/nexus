from __future__ import annotations

import re
from dataclasses import dataclass
from email.utils import parseaddr
from html import unescape

BUSINESS_DOMAINS = {
    "claronfibreoptics.com", "westcoastoptilinks.com", "stl.tech",
    "navank.in", "blspolymers.com", "workindia.in", "gem.gov.in",
}
BUSINESS_TERMS = {
    "invoice", "dispatch", "purchase order", "quotation", "rfq",
    "stock level", "reconciliation", "payment", "sales", "marketing",
    "production", "jobwork", "material", "supplier", "customer",
    "tender", "gst", "tax", "shipment", "freight", "delivery",
    "candidate", "interview", "hiring", "recruitment",
}
FAMILY_TERMS = {"school", "parent teacher", "family", "birthday", "daughter", "son", "spouse", "wife", "husband", "mother", "father", "medicine", "doctor", "hospital"}
PERSONAL_TERMS = {"courier", "hotel", "flight", "travel", "dentist", "subscription", "insurance", "utility bill", "appointment", "delivery arriving"}
PROMOTIONAL_TERMS = {"newsletter", "offer", "discount", "buy now", "webinar", "training program", "advertise", "expo", "exhibition", "campaign", "view in browser", "unsubscribe"}
URGENT_TERMS = {"urgent", "overdue", "failed", "declined", "final notice", "action required", "deadline", "immediate", "blocked", "suspended", "legal notice"}
FINANCE_TERMS = {"invoice", "payment", "credit", "debit", "gst", "tax", "reconciliation", "outstanding", "ledger", "statement", "receipt"}
PROCUREMENT_TERMS = {"purchase order", "rfq", "quotation", "material", "supplier", "dispatch", "shipment", "delivery date"}

@dataclass(slots=True)
class EmailInterpretation:
    domain: str
    category: str
    signal_score: int
    requires_decision: int
    priority: int
    confidence: float
    clean_summary: str
    entity_name: str | None
    relationship_impact: str


def _sender_domain(sender: str) -> str:
    _, address = parseaddr(sender or "")
    return address.rsplit("@", 1)[-1].lower() if "@" in address else ""


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"(?im)^content-(type|transfer-encoding|disposition):.*$", " ", text)
    text = re.sub(r"(?im)^mime-version:.*$", " ", text)
    text = re.sub(r"(?im)^this is a multi-part message in mime format.*$", " ", text)
    text = re.sub(r"(?m)^--[-=_A-Za-z0-9]+.*$", " ", text)
    text = re.sub(r"=[0-9A-Fa-f]{2}", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _best_summary(subject: str, body: str, sender: str) -> str:
    clean = _clean_text(body)
    if not clean:
        return f"Email from {parseaddr(sender or '')[0] or sender or 'unknown sender'}."
    parts = []
    for sentence in re.split(r"(?<=[.!?])\s+", clean):
        s = sentence.strip()
        if len(s) < 20:
            continue
        low = s.lower()
        if "view this email" in low or "unsubscribe" in low:
            continue
        parts.append(s)
        if len(" ".join(parts)) > 240:
            break
    summary = " ".join(parts) or clean
    return summary[:280] + ("…" if len(summary) > 280 else "")


def interpret_email(*, subject: str, body: str, sender: str) -> EmailInterpretation:
    subject = subject or "(No subject)"
    body = body or ""
    sender = sender or ""
    combined = f"{subject} {body} {sender}".lower()
    sender_domain = _sender_domain(sender)

    if sender_domain in BUSINESS_DOMAINS or any(term in combined for term in BUSINESS_TERMS):
        domain = "business"
    elif any(term in combined for term in FAMILY_TERMS):
        domain = "family"
    elif any(term in combined for term in PERSONAL_TERMS):
        domain = "personal"
    else:
        domain = "digital"

    if any(term in combined for term in FINANCE_TERMS):
        category = "finance"
    elif any(term in combined for term in PROCUREMENT_TERMS):
        category = "procurement"
    elif any(term in combined for term in {"candidate", "interview", "hiring", "recruitment"}):
        category = "recruitment"
    elif any(term in combined for term in {"production", "stock level", "coil report", "jobwork"}):
        category = "operations"
    elif any(term in combined for term in PROMOTIONAL_TERMS):
        category = "promotion"
    else:
        category = "communication"

    score = 35
    if domain == "business": score += 25
    if category in {"finance", "procurement", "operations"}: score += 20
    if category == "recruitment": score += 10
    if any(term in combined for term in URGENT_TERMS): score += 25
    if category == "promotion": score -= 45
    score = max(0, min(score, 100))

    needs_decision = int(score >= 80 or any(term in combined for term in URGENT_TERMS))
    priority = 1 if score >= 85 else 2 if score >= 65 else 3 if score >= 35 else 4
    confidence = 0.93 if sender_domain in BUSINESS_DOMAINS else 0.86 if domain != "digital" else 0.72

    sender_name, sender_address = parseaddr(sender)
    entity_name = sender_name.strip() or sender_address.strip() or None
    if any(term in combined for term in {"delay", "overdue", "complaint", "failed", "declined", "pending"}):
        relationship_impact = "negative"
    elif any(term in combined for term in {"confirmed", "received", "completed", "approved", "thank you"}):
        relationship_impact = "positive"
    else:
        relationship_impact = "neutral"

    return EmailInterpretation(domain, category, score, needs_decision, priority, confidence, _best_summary(subject, body, sender), entity_name, relationship_impact)
