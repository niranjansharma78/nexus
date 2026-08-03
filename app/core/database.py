from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "nexus.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            domain TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            entity_name TEXT,
            amount REAL,
            currency TEXT,
            requires_decision INTEGER NOT NULL DEFAULT 0,
            priority INTEGER NOT NULL DEFAULT 3
        );
        CREATE TABLE IF NOT EXISTS workspace_tiles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            domain TEXT NOT NULL,
            position INTEGER NOT NULL,
            size TEXT NOT NULL DEFAULT 'medium',
            pinned INTEGER NOT NULL DEFAULT 1,
            hidden INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            domain TEXT NOT NULL,
            health_score INTEGER NOT NULL DEFAULT 75,
            relationship_score INTEGER,
            trajectory TEXT NOT NULL DEFAULT 'stable',
            confidence REAL NOT NULL DEFAULT .5,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity_key TEXT NOT NULL,
            to_entity_key TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength INTEGER NOT NULL DEFAULT 50,
            trajectory TEXT NOT NULL DEFAULT 'stable',
            confidence REAL NOT NULL DEFAULT .5,
            updated_at TEXT NOT NULL,
            UNIQUE(from_entity_key,to_entity_key,relationship_type)
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            domain TEXT NOT NULL DEFAULT 'personal',
            pinned INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)
