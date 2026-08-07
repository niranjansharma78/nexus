from pathlib import Path

from app.brain.planning.repository import PlanRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    PlanRepository(database_path).ensure_schema()
    print(f"Planning Engine store ready: {database_path}")


if __name__ == "__main__":
    main()
