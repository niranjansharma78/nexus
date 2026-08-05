from pathlib import Path
from app.brain.learning.repository import LearningRepository

def main() -> None:
    database_path = Path("data") / "nexus.db"
    LearningRepository(database_path).ensure_schema()
    print(f"Learning Engine store ready: {database_path}")

if __name__ == "__main__":
    main()
