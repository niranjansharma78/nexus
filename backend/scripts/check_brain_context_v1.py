from pathlib import Path
from app.brain.core.context import BrainContextBuilder

def main() -> None:
    context = BrainContextBuilder(Path("data") / "nexus.db").build()
    print({
        "summary": context.summary,
        "confidence": context.confidence,
        "confidence_band": context.confidence_band,
    })

if __name__ == "__main__":
    main()
