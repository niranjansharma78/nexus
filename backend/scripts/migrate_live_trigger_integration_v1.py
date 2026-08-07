from pathlib import Path

from app.brain.triggers.repository import TriggerRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    TriggerRepository(database_path).ensure_schema()
    print(f"Live Trigger Integration store ready: {database_path}")


if __name__ == "__main__":
    main()
