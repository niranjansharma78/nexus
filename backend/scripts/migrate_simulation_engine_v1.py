from pathlib import Path
from app.brain.simulation.repository import SimulationRepository


def main() -> None:
    database_path = Path("data") / "nexus.db"
    SimulationRepository(database_path).ensure_schema()
    print(f"Simulation Engine store ready: {database_path}")


if __name__ == "__main__":
    main()
