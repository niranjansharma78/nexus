from pathlib import Path
from app.brain.context_engine.service import ContextEngine
from app.brain.ontology.models import UniversalEvent, UniversalObjectRef
from app.brain.ontology.transitions import UniversalTransition
from app.brain.persistence.universal_event_repository import UniversalEventRepository

def save_event(db: Path, event_id: str, label: str, world: str):
    UniversalEventRepository(db).save(UniversalEvent(
        event_id=event_id,
        object=UniversalObjectRef(kind="event", label=label),
        intent="observation",
        transition=UniversalTransition.OBSERVED,
        state="observed",
        world=world,
        confidence=0.8,
        source="test",
    ))

def test_context_requires_query(tmp_path: Path):
    try:
        ContextEngine(tmp_path / "brain.db").build("")
        assert False
    except ValueError:
        pass

def test_context_ranks_matching_event_first(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(db, "a", "Supplier payment overdue", "finance")
    save_event(db, "b", "Family dinner planned", "family")
    context = ContextEngine(db).build("supplier payment")
    assert context.items[0].reference_id == "a"

def test_context_respects_world_filter(tmp_path: Path):
    db = tmp_path / "brain.db"
    save_event(db, "a", "Machine stopped", "factory")
    save_event(db, "b", "Family meeting", "family")
    context = ContextEngine(db).build("meeting machine", world="family")
    assert all(item.world == "family" for item in context.items)
