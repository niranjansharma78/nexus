from datetime import datetime
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "nexus.db"
BACKUP_DIR = ROOT / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

if not SOURCE.exists():
    raise SystemExit("Database not found")

target = BACKUP_DIR / (
    "nexus_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".db"
)
shutil.copy2(SOURCE, target)
print(target)
