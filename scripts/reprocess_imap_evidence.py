from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from app.core.database import get_connection
from app.services.email_intelligence import interpret_email


def ensure_columns(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(evidence)").fetchall()}
    additions = {
        "category": "TEXT",
        "signal_score": "INTEGER NOT NULL DEFAULT 0",
        "relationship_impact": "TEXT NOT NULL DEFAULT 'neutral'",
    }
    for name, ddl in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE evidence ADD COLUMN {name} {ddl}")


def main():
    with get_connection() as conn:
        ensure_columns(conn)
        rows = conn.execute("SELECT id,title,summary,entity_name FROM evidence WHERE source='IMAP' ORDER BY id").fetchall()
        for row in rows:
            r = interpret_email(subject=row["title"], body=row["summary"], sender=row["entity_name"] or "")
            conn.execute("""
                UPDATE evidence SET summary=?,domain=?,confidence=?,requires_decision=?,priority=?,
                category=?,signal_score=?,relationship_impact=?,entity_name=? WHERE id=?
            """, (r.clean_summary,r.domain,r.confidence,r.requires_decision,r.priority,r.category,r.signal_score,r.relationship_impact,r.entity_name,row["id"]))
    print(f"Reprocessed {len(rows)} IMAP evidence records.")

if __name__ == "__main__": main()
