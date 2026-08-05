from __future__ import annotations

ACTION_PHRASES = {
    "confirmation required",
    "please confirm",
    "approval required",
    "please approve",
    "action required",
    "decision required",
    "please advise",
    "authorize",
    "accept",
    "reject",
    "select",
    "choose",
}

FOLLOWUP_TERMS = {
    "follow up",
    "follow-up",
    "pending",
    "awaiting",
    "overdue",
    "reminder",
    "status update",
    "please update",
    "please share",
    "please revert",
}

INFORMATION_TERMS = {
    "for your information",
    "fyi",
    "dispatch details",
    "payment received",
    "production confirmation",
    "stock levels",
    "invoice attached",
}

CONFIRMATION_TERMS = {
    "confirmed",
    "completed",
    "received",
    "dispatched",
    "shipped",
    "production confirmation",
    "payment confirmation",
}

RECRUITMENT_TERMS = {
    "candidate",
    "interview",
    "workindia",
    "sales manager",
    "resume",
    "cv",
}


def classify_attention(evidence: dict) -> dict:
    title = str(evidence.get("title") or "")
    summary = str(evidence.get("summary") or "")
    text = f"{title} {summary}".lower()

    category = str(evidence.get("category") or "").lower()
    signal_score = int(evidence.get("signal_score") or 0)
    brain_priority = int(evidence.get("brain_priority") or 0)

    is_recruitment = (
        category == "recruitment"
        or any(term in text for term in RECRUITMENT_TERMS)
    )
    explicit_action = any(phrase in text for phrase in ACTION_PHRASES)
    has_followup = any(term in text for term in FOLLOWUP_TERMS)
    looks_informational = any(term in text for term in INFORMATION_TERMS)
    looks_confirmed = any(term in text for term in CONFIRMATION_TERMS)

    if is_recruitment:
        return {
            "attention_type": "grouped",
            "requires_decision": False,
            "requires_followup": False,
            "attention_explanation": "Recruitment item grouped",
        }

    if looks_confirmed or looks_informational:
        if explicit_action:
            return {
                "attention_type": "decision",
                "requires_decision": True,
                "requires_followup": False,
                "attention_explanation": "Explicit action requested despite confirmation wording",
            }
        return {
            "attention_type": "information",
            "requires_decision": False,
            "requires_followup": False,
            "attention_explanation": "Confirmation or informational message",
        }

    if explicit_action and brain_priority >= 60:
        return {
            "attention_type": "decision",
            "requires_decision": True,
            "requires_followup": False,
            "attention_explanation": "Explicit action or judgement requested",
        }

    if has_followup and brain_priority >= 50:
        return {
            "attention_type": "follow_up",
            "requires_decision": False,
            "requires_followup": True,
            "attention_explanation": "Follow-up language detected",
        }

    if brain_priority >= 85 and signal_score >= 70:
        return {
            "attention_type": "decision",
            "requires_decision": True,
            "requires_followup": False,
            "attention_explanation": "Very high priority and signal score",
        }

    if brain_priority >= 60:
        return {
            "attention_type": "signal",
            "requires_decision": False,
            "requires_followup": False,
            "attention_explanation": "Material signal without direct decision",
        }

    return {
        "attention_type": "information",
        "requires_decision": False,
        "requires_followup": False,
        "attention_explanation": "No direct action required",
    }


def normalize_category(evidence: dict) -> str:
    title = str(evidence.get("title") or "")
    summary = str(evidence.get("summary") or "")
    text = f"{title} {summary}".lower()
    current = str(evidence.get("category") or "").strip().lower()

    # Stronger semantic categories override a generic existing category.
    if any(term in text for term in RECRUITMENT_TERMS):
        return "recruitment"
    if any(term in text for term in {"invoice", "payment", "reconciliation", "gst", "tax", "ledger"}):
        return "finance"
    if any(term in text for term in {"purchase order", " po ", "rfq", "quotation", "dispatch", "despatch", "shipment"}):
        return "procurement"
    if any(term in text for term in {"production", "stock level", "coil report", "jobwork"}):
        return "operations"
    if any(term in text for term in {"newsletter", "offer", "discount", "expo", "exhibition", "unsubscribe"}):
        return "promotion"

    return current or "communication"
