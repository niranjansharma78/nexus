from pathlib import Path
from app.brain.prediction.repository import PredictionRepository

if __name__ == "__main__":
    db = Path("data") / "nexus.db"
    PredictionRepository(db).ensure_schema()
    print(f"Prediction Engine store ready: {db}")
