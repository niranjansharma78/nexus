from pathlib import Path
from app.brain.curiosity.repository import CuriosityRepository

def main() -> None:
    database_path = Path("data") / "nexus.db"
    CuriosityRepository(database_path).ensure_schema()
    print(f"Curiosity Engine store ready: {database_path}")

if __name__ == "__main__":
    main()
