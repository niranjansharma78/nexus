from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr

from app.core.database import get_connection
from app.services.email_normalizer import clean_email_text


PROMOTIONAL_TERMS = {
    "amazon voucher",
    "gift voucher",
    "cashback offer",
    "discount",
    "promo code",
    "coupon",
    "reward points",
    "special offer",
    "limited period offer",
    "redeem now",
    "shopping voucher",
}

CHEQUE_BOUNCE_TERMS = {
    "cheque bounce",
    "cheque bounced",
    "cheque returned",
    "instrument returned",
    "return memo",
    "payment dishonoured",
    "payment dishonored",
}

CREDIT_TERMS = {
    "credited",
    "credit alert",
    "amount received",
    "deposited",
    "salary credited",
}

DEBIT_TERMS = {
    "debited",
    "debit alert",
    "amount paid",
    "withdrawn",
    "upi debit",
    "imps debit",
    "neft debit",
    "rtgs debit",
}

BANK_HINTS = {
    "idbi": "IDBI Bank",
    "sbi": "SBI",
    "statebankofindia": "SBI",
    "state bank of india": "SBI",
    "hdfc": "HDFC Bank",
    "icici": "ICICI Bank",
    "axis": "Axis Bank",
    "kotak": "Kotak Bank",
    "indusind": "IndusInd Bank",
    "yesbank": "YES Bank",
    "yes bank": "YES Bank",
    "bankofbaroda": "Bank of Baroda",
    "bank of baroda": "Bank of Baroda",
    "canarabank": "Canara Bank",
    "canara": "Canara Bank",
    "unionbank": "Union Bank",
    "union bank": "Union Bank",
    "pnb": "PNB",
    "punjabnationalbank": "PNB",
    "punjab national bank": "PNB",
    "federalbank": "Federal Bank",
    "federal bank": "Federal Bank",
}

AMOUNT_PATTERNS = [
    re.compile(
        r"(?:₹|rs\.?|inr)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:₹|inr)",
        re.IGNORECASE,
    ),
]

SOURCE_PATTERNS = [
    re.compile(
        r"\b(?:from|remitter|sender|received from|by)\s*[:\-]?\s*"
        r"([A-Za-z0-9@._&()/ -]{2,80})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:name of remitter|remitter name)\s*[:\-]?\s*"
        r"([A-Za-z0-9@._&()/ -]{2,80})",
        re.IGNORECASE,
    ),
]

DESTINATION_PATTERNS = [
    re.compile(
        r"\b(?:to|beneficiary|paid to|merchant)\s*[:\-]?\s*"
        r"([A-Za-z0-9@._&()/ -]{2,80})",
        re.IGNORECASE,
    ),
]


def _contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _is_promotional(text: str) -> bool:
    return _contains_any(text, PROMOTIONAL_TERMS)


def _direction(text: str) -> str:
    if _contains_any(text, CHEQUE_BOUNCE_TERMS):
        return "cheque_bounce"
    if _contains_any(text, CREDIT_TERMS):
        return "credit"
    if _contains_any(text, DEBIT_TERMS):
        return "debit"
    return "transaction"


def _amount(text: str) -> float | None:
    for pattern in AMOUNT_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            continue
    return None


def _sender_domain(sender: str | None) -> str:
    if not sender:
        return ""
    _, address = parseaddr(sender)
    if "@" in address:
        return address.split("@", 1)[1].lower()
    return sender.lower()


def _bank_name(
    text: str,
    sender: str | None = None,
    entity_name: str | None = None,
) -> str:
    haystack = " ".join(
        part
        for part in (
            text,
            sender or "",
            _sender_domain(sender),
            entity_name or "",
        )
        if part
    )
    normalized = (
        haystack.lower()
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )

    for hint, label in BANK_HINTS.items():
        normalized_hint = (
            hint.lower()
            .replace("-", "")
            .replace("_", "")
            .replace(".", "")
        )
        if normalized_hint in normalized:
            return label

    display_name, _ = parseaddr(sender or "")
    display_name = display_name.strip()
    if display_name and "bank" in display_name.lower():
        return display_name[:40]

    return "Bank"


def _clean_party(value: str | None) -> str | None:
    if not value:
        return None

    cleaned = re.sub(r"\s+", " ", value).strip(" .,:;-")
    cleaned = re.split(
        r"\b(?:on|dated|date|ref|reference|a/c|account|upi|neft|rtgs|imps|"
        r"txn|transaction|utr|available balance|avl bal)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip(" .,:;-")

    lowered = cleaned.lower()

    if "@" in cleaned and any(
        token in lowered
        for token in (
            "neft@",
            "alerts@",
            "alert@",
            "notify@",
            "noreply@",
            "no-reply@",
            "imps@",
            "rtgs@",
            "upi@",
        )
    ):
        return None

    if any(bank_hint in lowered for bank_hint in BANK_HINTS):
        return None

    if len(cleaned) < 2:
        return None

    return cleaned[:60]


def _counterparty(
    text: str,
    direction: str,
    entity_name: str | None,
) -> str | None:
    patterns = SOURCE_PATTERNS if direction == "credit" else DESTINATION_PATTERNS

    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue

        party = _clean_party(match.group(1))
        if party:
            return party

    return _clean_party(entity_name)


def _load_evidence(hours: int) -> list[dict]:
    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=max(1, min(hours, 720)))
    ).isoformat()

    with get_connection() as conn:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(evidence)").fetchall()
        }

        sender_select = "sender" if "sender" in columns else "NULL AS sender"
        message_id_select = (
            "message_id"
            if "message_id" in columns
            else "NULL AS message_id"
        )

        query = f"""
            SELECT
                id,
                title,
                summary,
                entity_name,
                occurred_at,
                {sender_select},
                {message_id_select}
            FROM evidence
            WHERE occurred_at >= ?
              AND (
                LOWER(COALESCE(title,'')) LIKE '%credited%'
                OR LOWER(COALESCE(summary,'')) LIKE '%credited%'
                OR LOWER(COALESCE(title,'')) LIKE '%debited%'
                OR LOWER(COALESCE(summary,'')) LIKE '%debited%'
                OR LOWER(COALESCE(title,'')) LIKE '%upi%'
                OR LOWER(COALESCE(summary,'')) LIKE '%upi%'
                OR LOWER(COALESCE(title,'')) LIKE '%neft%'
                OR LOWER(COALESCE(summary,'')) LIKE '%neft%'
                OR LOWER(COALESCE(title,'')) LIKE '%rtgs%'
                OR LOWER(COALESCE(summary,'')) LIKE '%rtgs%'
                OR LOWER(COALESCE(title,'')) LIKE '%imps%'
                OR LOWER(COALESCE(summary,'')) LIKE '%imps%'
                OR LOWER(COALESCE(title,'')) LIKE '%cheque bounce%'
                OR LOWER(COALESCE(summary,'')) LIKE '%cheque bounce%'
                OR LOWER(COALESCE(title,'')) LIKE '%cheque returned%'
                OR LOWER(COALESCE(summary,'')) LIKE '%cheque returned%'
                OR LOWER(COALESCE(title,'')) LIKE '%dishonour%'
                OR LOWER(COALESCE(summary,'')) LIKE '%dishonour%'
              )
            ORDER BY id DESC
            LIMIT 150
        """

        rows = conn.execute(query, (since,)).fetchall()

    return [dict(row) for row in rows]



def _compact_summary(
    direction: str,
    amount: float | None,
    counterparty: str | None,
    title: str,
) -> str:
    amount_text = (
        f"₹{amount:,.2f}".replace(".00", "")
        if amount is not None
        else "Amount not detected"
    )

    if direction == "credit":
        return amount_text + " credited" + (
            f" from {counterparty}" if counterparty else ""
        )

    if direction == "debit":
        return amount_text + " debited" + (
            f" to {counterparty}" if counterparty else ""
        )

    if direction == "cheque_bounce":
        return "Cheque bounce" + (
            f" involving {counterparty}" if counterparty else ""
        )

    return title or "Bank transaction"


def _compact_label(
    *,
    direction: str,
    bank: str,
    counterparty: str | None,
) -> str:
    label = {
        "credit": "Credit",
        "debit": "Debit",
        "cheque_bounce": "Cheque Bounce",
    }.get(direction, "Transaction")

    return f"{label} · {bank}" + (
        f" · {counterparty}" if counterparty else ""
    )

def banking_highlights(hours: int = 72, limit: int = 5) -> dict:
    rows = _load_evidence(hours)

    items: list[dict] = []
    seen_message_ids: set[str] = set()
    seen_fallback: set[tuple] = set()

    total_credit = 0.0
    total_debit = 0.0
    bounce_count = 0

    for row in rows:
        combined = clean_email_text(
            f"{row.get('title','')} {row.get('summary','')}"
        )

        if _is_promotional(combined):
            continue

        direction = _direction(combined)
        if direction == "transaction":
            continue

        amount = _amount(combined)
        bank = _bank_name(
            combined,
            row.get("sender"),
            row.get("entity_name"),
        )
        counterparty = _counterparty(
            combined,
            direction,
            row.get("entity_name"),
        )

        message_id = (row.get("message_id") or "").strip().lower()

        if message_id:
            if message_id in seen_message_ids:
                continue
            seen_message_ids.add(message_id)
        else:
            fallback_key = (
                direction,
                amount,
                bank.lower(),
                (counterparty or "").lower(),
                str(row.get("occurred_at") or "")[:16],
            )
            if fallback_key in seen_fallback:
                continue
            seen_fallback.add(fallback_key)

        if direction == "credit" and amount is not None:
            total_credit += amount
        elif direction == "debit" and amount is not None:
            total_debit += amount
        elif direction == "cheque_bounce":
            bounce_count += 1

        items.append({
            "id": row["id"],
            "direction": direction,
            "amount": amount,
            "bank": bank,
            "source": counterparty or "Source not identified",
            "occurred_at": row.get("occurred_at"),
            "critical": direction == "cheque_bounce",
        })

    items = items[:max(1, min(limit, 5))]

    return {
        "count": len(items),
        "totals": {
            "credit": round(total_credit, 2),
            "debit": round(total_debit, 2),
            "bounce_count": bounce_count,
        },
        "items": items,
    }
