from pathlib import Path

from app.brain.persistence.universal_event_repository import (
    UniversalEventRepository,
)


def main() -> None:
    database_path = Path("data") / "nexus.db"
    repository = UniversalEventRepository(database_path)
    repository.ensure_schema()
    print(f"Universal event store ready: {database_path}")


if __name__ == "__main__":
    main()
