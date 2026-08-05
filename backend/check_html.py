from app.core.database import get_connection

conn = get_connection()

rows = conn.execute("""
SELECT id, title, summary
FROM evidence
WHERE summary LIKE '%DOCTYPE%'
   OR summary LIKE '%<html%'
   OR summary LIKE '%Content-Type%'
ORDER BY id DESC
LIMIT 20
""").fetchall()

print(f"Found {len(rows)} records\n")

for row in rows:
    print("=" * 80)
    print("ID:", row["id"])
    print("TITLE:", row["title"])
    print("SUMMARY:", row["summary"][:300])
    print()

conn.close()