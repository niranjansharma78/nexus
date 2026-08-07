from pathlib import Path

from app.brain.attention.repository import AttentionRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    AttentionRepository(database_path).ensure_schema()
    print(f"Attention Engine store ready: {database_path}")


if __name__ == "__main__":
    main()
