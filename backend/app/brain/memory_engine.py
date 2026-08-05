from app.core.database import get_connection

def ensure_memory_tables():
    with get_connection() as conn:
        conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS nexus_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                entity_name TEXT,
                importance INTEGER NOT NULL DEFAULT 50,
                confidence REAL NOT NULL DEFAULT 0.75,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_nexus_memory_entity ON nexus_memory(entity_name);
            '''
        )

def remember(memory_type, title, content, entity_name=None, importance=50, confidence=0.75):
    ensure_memory_tables()
    with get_connection() as conn:
        cur = conn.execute(
            '''INSERT INTO nexus_memory(memory_type,title,content,entity_name,importance,confidence)
               VALUES(?,?,?,?,?,?)''',
            (memory_type, title, content, entity_name, max(0,min(int(importance),100)), max(0,min(float(confidence),1))),
        )
        return int(cur.lastrowid)

def recent_memories(limit=20):
    ensure_memory_tables()
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM nexus_memory ORDER BY importance DESC,id DESC LIMIT ?",
            (max(1,min(limit,200)),)
        )]
