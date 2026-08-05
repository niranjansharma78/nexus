from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.brain.executive_brief_engine import build_executive_brief
from app.brain.relationship_engine import build_relationship_snapshots
from app.core.database import get_connection
from app.services.brain_calibration_service import (
    calibrate_brain,
    grouped_recruitment_summary,
)
from app.services.delegation_service import ensure_delegation_schema


def _monitor_status_map(conn) -> dict[int, str]:
    try:
        rows = conn.execute(
            """
            SELECT evidence_id, status
            FROM nexus_monitor_actions
            """
        ).fetchall()
        return {int(row["evidence_id"]): str(row["status"]) for row in rows}
    except Exception:
        return {}


def _open_delegation_evidence_ids(conn) -> set[int]:
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT evidence_id
            FROM nexus_delegations
            WHERE evidence_id IS NOT NULL
              AND status IN ('open','in_progress')
            """
        ).fetchall()
        return {int(row["evidence_id"]) for row in rows}
    except Exception:
        return set()


def executive_brief(hours: int = 24) -> dict:
    calibrate_brain()
    ensure_delegation_schema()

    since = (
        datetime.now(timezone.utc)
        - timedelta(hours=max(1, min(hours, 168)))
    ).isoformat()

    with get_connection() as conn:
        recent = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM evidence
                WHERE occurred_at >= ?
                ORDER BY id DESC
                """,
                (since,),
            ).fetchall()
        ]

        all_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT *
                FROM evidence
                ORDER BY id DESC
                LIMIT 1000
                """
            ).fetchall()
        ]

        monitor_status = _monitor_status_map(conn)
        delegated_ids = _open_delegation_evidence_ids(conn)

    relationships = build_relationship_snapshots(all_rows)
    declining = [
        item
        for item in relationships
        if item.get("direction") == "declining"
    ]

    brief = build_executive_brief(
        recent_items=recent,
        grouped_recruitment=grouped_recruitment_summary(500),
        declining_relationships=declining,
    )

    # Hide updates the user has already acknowledged or closed.
    brief["monitor"] = [
        item
        for item in brief["monitor"]
        if monitor_status.get(int(item["id"])) not in {"acknowledged", "closed"}
    ]

    # Mark monitored items already converted into delegations.
    for item in brief["monitor"]:
        evidence_id = item.get("id")
        item["delegated"] = bool(
            evidence_id is not None and int(evidence_id) in delegated_ids
        )

    for item in brief["delegate"]:
        evidence_id = item.get("id")
        item["delegated"] = bool(
            evidence_id is not None and int(evidence_id) in delegated_ids
        )

    brief["summary"]["monitor"] = len(brief["monitor"])
    brief["summary"]["delegate"] = len(brief["delegate"])

    if brief["needs_you"]:
        brief["headline"] = (
            f"{len(brief['needs_you'])} item"
            f"{'s' if len(brief['needs_you']) != 1 else ''} need your judgement."
        )
    elif brief["delegate"]:
        brief["headline"] = (
            f"{len(brief['delegate'])} item"
            f"{'s' if len(brief['delegate']) != 1 else ''} should be delegated."
        )
    elif brief["monitor"]:
        brief["headline"] = (
            f"{len(brief['monitor'])} important update"
            f"{'s' if len(brief['monitor']) != 1 else ''} are worth knowing."
        )
    else:
        brief["headline"] = "Everything important is under control."

    return brief
