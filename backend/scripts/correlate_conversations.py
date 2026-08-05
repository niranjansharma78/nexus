from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.conversation_engine_service import correlate_unlinked_events


print(correlate_unlinked_events(limit=5000))
