from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import init_db
from app.core.migrations import run_migrations


init_db()
applied = run_migrations()
print("Applied migrations:", applied if applied else "none")
