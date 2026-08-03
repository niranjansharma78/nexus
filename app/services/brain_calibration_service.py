from __future__ import annotations

from collections import defaultdict

from app.brain.decision_engine import classify_attention, normalize_category
from app.brain.priority_engine import score_evidence
from app.core.database import get_connection


def ensure_calibration_schema() -> None:
    with get_connection() as conn:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(evidence)").fetchall()}
        additions = {
            "attention_type": "TEXT NOT NULL DEFAULT 'information'",
            "requires_followup": "INTEGER NOT NULL DEFAULT 0",
            "attention_explanation": "TEXT",
        }
        for name, ddl in additions.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE evidence ADD COLUMN {name} {ddl}")


def calibrate_brain(limit: int = 1000) -> dict:
    ensure_calibration_schema()

    with get_connection() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM evidence ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 5000)),),
            ).fetchall()
        ]

        updated = 0
        for row in rows:
            # Clear legacy judgement before recalculating priority.
            row["requires_decision"] = 0

            category = normalize_category(row)
            row["category"] = category

            priority = score_evidence(row)
            row["brain_priority"] = priority["score"]

            attention = classify_attention(row)

            # Information and grouped items should not retain inflated priority.
            calibrated_priority = priority["score"]
            calibrated_band = priority["band"]
            if attention["attention_type"] == "information":
                calibrated_priority = min(calibrated_priority, 49)
                calibrated_band = "medium" if calibrated_priority >= 35 else "low"
            elif attention["attention_type"] == "grouped":
                calibrated_priority = min(calibrated_priority, 34)
                calibrated_band = "low"

            conn.execute(
                """
                UPDATE evidence
                SET category=?,
                    brain_priority=?,
                    brain_band=?,
                    brain_explanation=?,
                    attention_type=?,
                    requires_decision=?,
                    requires_followup=?,
                    attention_explanation=?
                WHERE id=?
                """,
                (
                    category,
                    calibrated_priority,
                    calibrated_band,
                    " | ".join(priority["explanation"]),
                    attention["attention_type"],
                    int(attention["requires_decision"]),
                    int(attention["requires_followup"]),
                    attention["attention_explanation"],
                    row["id"],
                ),
            )
            updated += 1

    return {"ok": True, "updated": updated}


def grouped_recruitment_summary(limit: int = 1000) -> list[dict]:
    ensure_calibration_schema()

    with get_connection() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM evidence
                WHERE category='recruitment'
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, min(limit, 5000)),),
            ).fetchall()
        ]

    grouped = defaultdict(list)
    for row in rows:
        day = str(row.get("occurred_at") or "")[:10]
        grouped[day].append(row)

    return [
        {
            "date": day,
            "count": len(items),
            "title": f"{len(items)} recruitment item{'s' if len(items) != 1 else ''} received",
            "summary": "Grouped candidate and interview notifications.",
            "attention_type": "grouped",
            "requires_decision": False,
        }
        for day, items in sorted(grouped.items(), reverse=True)
    ][:10]
