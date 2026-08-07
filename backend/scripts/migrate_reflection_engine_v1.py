from pathlib import Path

from app.brain.reflection.repository import ReflectionRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    ReflectionRepository(database_path).ensure_schema()
    print(f"Reflection Engine store ready: {database_path}")


if __name__ == "__main__":
    main()
