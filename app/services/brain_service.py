from datetime import datetime, timedelta, timezone
from app.core.database import get_connection
from app.brain.priority_engine import score_evidence
from app.brain.relationship_engine import build_relationship_snapshots
from app.services.brain_calibration_service import calibrate_brain, grouped_recruitment_summary
from app.brain.memory_engine import ensure_memory_tables, recent_memories

def ensure_brain_schema():
    ensure_memory_tables()
    with get_connection() as conn:
        existing = {r[1] for r in conn.execute("PRAGMA table_info(evidence)").fetchall()}
        additions = {
            "category":"TEXT",
            "signal_score":"INTEGER NOT NULL DEFAULT 0",
            "relationship_impact":"TEXT NOT NULL DEFAULT 'neutral'",
            "brain_priority":"INTEGER NOT NULL DEFAULT 0",
            "brain_band":"TEXT NOT NULL DEFAULT 'low'",
            "brain_explanation":"TEXT",
        }
        for name, ddl in additions.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE evidence ADD COLUMN {name} {ddl}")

def refresh_brain(limit=500):
    ensure_brain_schema()
    with get_connection() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY id DESC LIMIT ?", (max(1,min(limit,5000)),))]
        for row in rows:
            result = score_evidence(row)
            conn.execute(
                '''UPDATE evidence SET brain_priority=?,brain_band=?,brain_explanation=?,
                   requires_decision=CASE WHEN ?=1 THEN 1 ELSE requires_decision END WHERE id=?''',
                (result["score"], result["band"], " | ".join(result["explanation"]), int(result["requires_decision"]), row["id"])
            )
    return {"ok": True, "updated": len(rows)}

def brain_state():
    ensure_brain_schema()
    refresh_brain()
    calibrate_brain()
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    with get_connection() as conn:
        recent = [dict(r) for r in conn.execute(
            "SELECT * FROM evidence WHERE occurred_at>=? ORDER BY brain_priority DESC,id DESC", (since,)
        )]
        all_rows = [dict(r) for r in conn.execute("SELECT * FROM evidence ORDER BY id DESC LIMIT 1000")]

    reviewed = len(recent)
    signals = sum(1 for r in recent if r.get("attention_type") in {"signal","follow_up","decision"})
    decisions = sum(1 for r in recent if int(r.get("requires_decision") or 0) == 1)
    ignored = max(0, reviewed-signals)
    rel = build_relationship_snapshots(all_rows)
    declining = [x for x in rel if x["direction"]=="declining"][:5]

    if decisions:
        summary = f"I reviewed {reviewed} recent items. {decisions} need your judgement."
    elif signals:
        summary = f"I reviewed {reviewed} recent items. Nothing urgent, but {signals} signals changed."
    else:
        summary = "Everything important is under control."

    confidence = round(sum(float(r.get("confidence") or 0) for r in recent)/reviewed*100) if reviewed else 100

    return {
        "brain":{"state":"thinking" if reviewed else "monitoring","health":"healthy","confidence":confidence},
        "morning_brief":{
            "reviewed":reviewed,"ignored":ignored,"signals":signals,"decisions":decisions,
            "estimated_minutes_saved":max(5,reviewed*2),"summary":summary
        },
        "decisions":[r for r in recent if int(r.get("requires_decision") or 0)==1][:5],
        "signals":[r for r in recent if r.get("attention_type") in {"signal","follow_up","decision"}][:8],
        "declining_relationships":declining,
        "grouped_recruitment": grouped_recruitment_summary(200),
        "memories":recent_memories(8),
    }
