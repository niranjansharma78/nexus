URGENT_TERMS = {
    "urgent", "overdue", "failed", "declined", "deadline",
    "action required", "legal notice", "blocked", "suspended",
}
HIGH_IMPACT = {"finance", "procurement", "operations", "compliance"}

def score_evidence(evidence: dict) -> dict:
    score = int(evidence.get("signal_score") or 0)
    reasons = []
    category = str(evidence.get("category") or "").lower()
    text = f"{evidence.get('title','')} {evidence.get('summary','')}".lower()

    if category in HIGH_IMPACT:
        score += 12
        reasons.append(f"High-impact category: {category}")
    if evidence.get("domain") == "family":
        score += 8
        reasons.append("Family evidence")
    if evidence.get("relationship_impact") == "negative":
        score += 12
        reasons.append("Negative relationship impact")
    if evidence.get("requires_decision"):
        score += 20
        reasons.append("Already marked for judgement")
    if any(term in text for term in URGENT_TERMS):
        score += 20
        reasons.append("Urgent language detected")
    if float(evidence.get("confidence") or 0) < 0.65:
        score -= 8
        reasons.append("Lower confidence")

    score = max(0, min(score, 100))
    band = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 35 else "low"
    return {
        "score": score,
        "band": band,
        "requires_decision": score >= 80,
        "explanation": reasons or ["No material priority factors"],
    }
