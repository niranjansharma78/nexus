from app.brain.context_engine.models import ContextItem,ContextKind
from app.brain.memory.models import MemoryClass,MemoryDecision
from app.brain.memory.salience import SalienceEngine

def item(kind=ContextKind.EVENT,relevance=.8,confidence=.8): return ContextItem(kind=kind,reference_id='r1',label='Important',relevance=relevance,confidence=confidence)
def test_high_salience_event_becomes_episodic(): assert SalienceEngine().evaluate(item()).memory_class==MemoryClass.EPISODIC
def test_repeated_learning_becomes_semantic(): assert SalienceEngine().evaluate(item(ContextKind.LEARNING),repeated_count=3).memory_class==MemoryClass.SEMANTIC
def test_aspiration_preserved_for_review():
 x=SalienceEngine().evaluate(item(relevance=.2,confidence=.4),aspiration_signal=True); assert x.memory_class==MemoryClass.DORMANT_ASPIRATION and x.decision==MemoryDecision.REVIEW
def test_identity_never_auto_promotes(): assert SalienceEngine().evaluate(item(),identity_sensitive=True).decision==MemoryDecision.REVIEW
