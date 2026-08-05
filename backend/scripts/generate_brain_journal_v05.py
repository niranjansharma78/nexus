from pathlib import Path

from app.brain.journal.service import BrainJournalService


def main() -> None:
    database_path = Path("data") / "nexus.db"
    service = BrainJournalService(database_path)
    entry = service.build_daily_entry()
    print(entry.to_dict())


if __name__ == "__main__":
    main()
