from pathlib import Path

from app.brain.decision.repository import DecisionRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    DecisionRepository(database_path).ensure_schema()
    print(f"Decision Engine store ready: {database_path}")


if __name__ == "__main__":
    main()
