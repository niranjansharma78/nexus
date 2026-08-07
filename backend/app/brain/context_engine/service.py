from pathlib import Path
from app.brain.core.context import BrainContextBuilder
from .models import ContextItem, ContextKind, WorkingContext

class ContextEngine:
    def __init__(self, database_path: str | Path):
        self.builder = BrainContextBuilder(database_path)

    def build(self, query: str, *, world: str | None = None, max_items: int = 20):
        if not query.strip():
            raise ValueError("query is required")
        brain = self.builder.build(event_limit=300, learning_limit=100, question_limit=100, journal_limit=30)
        terms = {term.casefold() for term in query.split() if len(term.strip()) >= 3}
        candidates = []
        for event in brain.events:
            if world and event.get("world") != world:
                continue
            text = str(event).casefold()
            overlap = sum(term in text for term in terms)
            relevance = min(1.0, overlap / max(1, len(terms)) + float(event.get("confidence", 0)) * 0.2)
            if relevance <= 0:
                continue
            candidates.append(ContextItem(
                kind=ContextKind.EVENT,
                reference_id=event["event_id"],
                label=event.get("object", {}).get("label", "Untitled"),
                relevance=round(relevance, 10),
                confidence=float(event.get("confidence", 0)),
                occurred_at=event.get("occurred_at"),
                world=event.get("world"),
                source=event.get("source"),
                reason="Matched current query and confidence.",
            ))
        candidates.sort(key=lambda item: (item.relevance, item.confidence), reverse=True)
        selected = candidates[:max(1, min(max_items, 100))]
        return WorkingContext(query=query, items=selected, world=world, summary={
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "event_count": len(selected),
        })
