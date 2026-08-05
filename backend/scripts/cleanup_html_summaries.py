from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.core.database import get_connection
from app.services.email_normalizer import safe_summary


with get_connection() as conn:
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT id,title,summary,category,entity_name
            FROM evidence
            WHERE LOWER(COALESCE(summary,'')) LIKE '%<!doctype%'
               OR LOWER(COALESCE(summary,'')) LIKE '%<html%'
               OR LOWER(COALESCE(summary,'')) LIKE '%<body%'
               OR LOWER(COALESCE(summary,'')) LIKE '%content-type%'
               OR LOWER(COALESCE(summary,'')) LIKE '%font-family%'
            ORDER BY id
            """
        ).fetchall()
    ]

    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / (
        "html_summary_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )
    backup_path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for row in rows:
        cleaned = safe_summary(
            row.get("title"),
            row.get("summary"),
            row.get("category"),
            row.get("entity_name"),
        )
        conn.execute(
            "UPDATE evidence SET summary=? WHERE id=?",
            (cleaned, row["id"]),
        )

print(f"Backed up {len(rows)} records to {backup_path}")
print(f"Cleaned {len(rows)} malformed summaries.")
