from pathlib import Path

from app.brain.journal.repository import BrainJournalRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    repository = BrainJournalRepository(database_path)
    repository.ensure_schema()
    print(f"Brain Journal store ready: {database_path}")


if __name__ == "__main__":
    main()
