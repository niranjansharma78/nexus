from __future__ import annotations

from datetime import datetime, timedelta, timezone
from app.core.database import get_connection


def _safe_columns(conn) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(evidence)").fetchall()}
    additions = {
        "category": "TEXT",
        "signal_score": "INTEGER NOT NULL DEFAULT 0",
        "relationship_impact": "TEXT NOT NULL DEFAULT 'neutral'",
    }
    for name, ddl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE evidence ADD COLUMN {name} {ddl}")


def dashboard_intelligence() -> dict:
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    with get_connection() as conn:
        _safe_columns(conn)
        reviewed_24h = conn.execute("SELECT COUNT(*) FROM evidence WHERE occurred_at >= ?", (since,)).fetchone()[0]
        new_imap_24h = conn.execute("SELECT COUNT(*) FROM evidence WHERE source='IMAP' AND occurred_at >= ?", (since,)).fetchone()[0]
        high_signal_24h = conn.execute("SELECT COUNT(*) FROM evidence WHERE occurred_at >= ? AND COALESCE(signal_score,0) >= 70", (since,)).fetchone()[0]
        decisions_24h = conn.execute("SELECT COUNT(*) FROM evidence WHERE occurred_at >= ? AND requires_decision=1", (since,)).fetchone()[0]
        categories = [dict(r) for r in conn.execute("SELECT COALESCE(category,'uncategorized') category, COUNT(*) count FROM evidence WHERE occurred_at >= ? GROUP BY COALESCE(category,'uncategorized') ORDER BY count DESC LIMIT 6", (since,)).fetchall()]
        signals = [dict(r) for r in conn.execute("SELECT id,title,summary,domain,source,entity_name,confidence,requires_decision,priority,COALESCE(category,'uncategorized') category,COALESCE(signal_score,0) signal_score,COALESCE(relationship_impact,'neutral') relationship_impact,occurred_at FROM evidence WHERE COALESCE(signal_score,0) >= 50 ORDER BY requires_decision DESC, signal_score DESC, id DESC LIMIT 8").fetchall()]
    return {
        "reviewed_24h": reviewed_24h,
        "new_imap_24h": new_imap_24h,
        "high_signal_24h": high_signal_24h,
        "decisions_24h": decisions_24h,
        "categories": categories,
        "signals": signals,
        "estimated_minutes_saved": max(10, reviewed_24h * 2),
    }
