from pathlib import Path

from app.brain.perception.repository import EvidenceRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    EvidenceRepository(database_path).ensure_schema()
    print(f"Perception evidence store ready: {database_path}")


if __name__ == "__main__":
    main()
