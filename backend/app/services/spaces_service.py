from __future__ import annotations

from app.core.database import get_connection


DEFAULT_SPACES = [
    ("Personal", "personal", "Personal life and private accounts"),
    ("Family", "family", "Family and household"),
    ("Claron", "business", "Claron Fibreoptics"),
    ("Congen", "business", "Congen Products"),
    ("Tekhelsoft", "digital", "Software products and Nexus"),
]

VALID_WORLDS = {"business", "family", "personal", "digital", "custom"}


def ensure_spaces_schema() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS nexus_spaces(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              world TEXT NOT NULL,
              description TEXT,
              color_key TEXT,
              icon_key TEXT,
              sort_order INTEGER NOT NULL DEFAULT 100,
              is_default INTEGER NOT NULL DEFAULT 0,
              allow_cross_world INTEGER NOT NULL DEFAULT 0,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS mailbox_space_links(
              mailbox_profile_id INTEGER NOT NULL UNIQUE,
              space_id INTEGER NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(nexus_spaces)"
            ).fetchall()
        }

        additions = {
            "color_key": "TEXT",
            "icon_key": "TEXT",
            "sort_order": "INTEGER NOT NULL DEFAULT 100",
            "is_default": "INTEGER NOT NULL DEFAULT 0",
            "allow_cross_world": "INTEGER NOT NULL DEFAULT 0",
            "updated_at": "TEXT",
        }

        for name, declaration in additions.items():
            if name not in columns:
                conn.execute(
                    f"ALTER TABLE nexus_spaces ADD COLUMN {name} {declaration}"
                )

        for row in DEFAULT_SPACES:
            conn.execute(
                """
                INSERT OR IGNORE INTO nexus_spaces(name,world,description)
                VALUES(?,?,?)
                """,
                row,
            )


def _validate(
    *,
    name: str,
    world: str,
) -> tuple[str, str]:
    clean_name = name.strip()
    clean_world = world.strip().lower()

    if not clean_name:
        raise ValueError("World name is required")

    if clean_world not in VALID_WORLDS:
        raise ValueError("Invalid world type")

    return clean_name, clean_world


def list_spaces(
    *,
    include_archived: bool = False,
) -> list[dict]:
    ensure_spaces_schema()
    where = "" if include_archived else "WHERE s.is_active=1"

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT
                s.*,
                COUNT(msl.mailbox_profile_id) AS mailbox_count
            FROM nexus_spaces s
            LEFT JOIN mailbox_space_links msl
              ON msl.space_id=s.id
            {where}
            GROUP BY s.id
            ORDER BY
                s.is_default DESC,
                s.sort_order,
                s.name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def create_space(
    name: str,
    world: str,
    description: str | None = None,
    color_key: str | None = None,
    icon_key: str | None = None,
    allow_cross_world: bool = False,
) -> dict:
    ensure_spaces_schema()
    clean_name, clean_world = _validate(name=name, world=world)

    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO nexus_spaces(
                    name,
                    world,
                    description,
                    color_key,
                    icon_key,
                    allow_cross_world,
                    updated_at
                )
                VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)
                """,
                (
                    clean_name,
                    clean_world,
                    description,
                    color_key,
                    icon_key,
                    int(allow_cross_world),
                ),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("A World with this name already exists") from exc
            raise

        space_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]

        return dict(
            conn.execute(
                "SELECT * FROM nexus_spaces WHERE id=?",
                (space_id,),
            ).fetchone()
        )


def update_space(
    space_id: int,
    *,
    name: str,
    world: str,
    description: str | None = None,
    color_key: str | None = None,
    icon_key: str | None = None,
    allow_cross_world: bool = False,
) -> dict:
    ensure_spaces_schema()
    clean_name, clean_world = _validate(name=name, world=world)

    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM nexus_spaces WHERE id=?",
            (space_id,),
        ).fetchone():
            raise ValueError("World not found")

        try:
            conn.execute(
                """
                UPDATE nexus_spaces
                SET name=?,
                    world=?,
                    description=?,
                    color_key=?,
                    icon_key=?,
                    allow_cross_world=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    clean_name,
                    clean_world,
                    description,
                    color_key,
                    icon_key,
                    int(allow_cross_world),
                    space_id,
                ),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("A World with this name already exists") from exc
            raise

        return dict(
            conn.execute(
                "SELECT * FROM nexus_spaces WHERE id=?",
                (space_id,),
            ).fetchone()
        )


def set_default_space(space_id: int) -> dict:
    ensure_spaces_schema()

    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM nexus_spaces WHERE id=? AND is_active=1",
            (space_id,),
        ).fetchone():
            raise ValueError("World not found")

        conn.execute("UPDATE nexus_spaces SET is_default=0")
        conn.execute(
            """
            UPDATE nexus_spaces
            SET is_default=1,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (space_id,),
        )

    return {"ok": True, "space_id": space_id}


def delete_or_archive_space(
    space_id: int,
    *,
    move_to_space_id: int | None = None,
) -> dict:
    """Delete an empty World or archive a populated World safely."""
    ensure_spaces_schema()

    with get_connection() as conn:
        space = conn.execute(
            "SELECT * FROM nexus_spaces WHERE id=?",
            (space_id,),
        ).fetchone()

        if not space:
            raise ValueError("World not found")

        mailbox_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM mailbox_space_links
            WHERE space_id=?
            """,
            (space_id,),
        ).fetchone()["count"]

        if move_to_space_id is not None:
            if move_to_space_id == space_id:
                raise ValueError("Choose a different destination World")

            if not conn.execute(
                """
                SELECT id
                FROM nexus_spaces
                WHERE id=? AND is_active=1
                """,
                (move_to_space_id,),
            ).fetchone():
                raise ValueError("Destination World not found")

            conn.execute(
                """
                UPDATE mailbox_space_links
                SET space_id=?
                WHERE space_id=?
                """,
                (move_to_space_id, space_id),
            )
            mailbox_count = 0

        if mailbox_count > 0:
            conn.execute(
                """
                UPDATE nexus_spaces
                SET is_active=0,
                    is_default=0,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (space_id,),
            )
            return {
                "ok": True,
                "action": "archived",
                "space_id": space_id,
                "mailbox_count": mailbox_count,
            }

        conn.execute(
            "DELETE FROM mailbox_space_links WHERE space_id=?",
            (space_id,),
        )
        conn.execute(
            "DELETE FROM nexus_spaces WHERE id=?",
            (space_id,),
        )

        return {
            "ok": True,
            "action": "deleted",
            "space_id": space_id,
        }


def list_mailboxes_with_spaces() -> list[dict]:
    ensure_spaces_schema()

    with get_connection() as conn:
        try:
            rows = conn.execute(
                """
                SELECT
                    mp.id,
                    mp.label,
                    mp.host,
                    mp.port,
                    mp.username,
                    mp.folder,
                    mp.use_ssl,
                    mp.last_scan_at,
                    mp.last_scan_count,
                    s.id AS space_id,
                    s.name AS space_name,
                    s.world AS space_world
                FROM mailbox_profiles mp
                LEFT JOIN mailbox_space_links msl
                  ON msl.mailbox_profile_id=mp.id
                LEFT JOIN nexus_spaces s
                  ON s.id=msl.space_id
                ORDER BY mp.id DESC
                """
            ).fetchall()
        except Exception:
            rows = []

    return [dict(row) for row in rows]


def assign_mailbox_to_space(
    mailbox_profile_id: int,
    space_id: int,
) -> dict:
    ensure_spaces_schema()

    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM mailbox_profiles WHERE id=?",
            (mailbox_profile_id,),
        ).fetchone():
            raise ValueError("Mailbox profile not found")

        if not conn.execute(
            """
            SELECT id
            FROM nexus_spaces
            WHERE id=? AND is_active=1
            """,
            (space_id,),
        ).fetchone():
            raise ValueError("World not found")

        conn.execute(
            """
            INSERT INTO mailbox_space_links(mailbox_profile_id,space_id)
            VALUES(?,?)
            ON CONFLICT(mailbox_profile_id)
            DO UPDATE SET space_id=excluded.space_id
            """,
            (mailbox_profile_id, space_id),
        )

    return {
        "ok": True,
        "mailbox_profile_id": mailbox_profile_id,
        "space_id": space_id,
    }
