from app.brain.core.context import BrainContext
from app.brain.executive_reasoning.models import DecisionKind
from app.brain.executive_reasoning.service import ExecutiveReasoningEngine

def test_failed_open_event_becomes_risk():
    context=BrainContext(events=[{"event_id":"e1","object":{"label":"Failed settlement"},"transition":"failed","closure":"open","confidence":.9,"evidence_id":1}])
    d=ExecutiveReasoningEngine().reason(context)[0]
    assert d.kind==DecisionKind.RISK and d.why_now and d.evidence_ids==[1]

def test_open_commitment_becomes_action():
    context=BrainContext(events=[{"event_id":"e1","object":{"label":"Customer request"},"transition":"requested","closure":"open","confidence":.8,"evidence_id":None}])
    d=ExecutiveReasoningEngine().reason(context)[0]
    assert d.kind==DecisionKind.ACTION and d.recommended_action is not None

def test_open_question_becomes_action():
    context=BrainContext(open_questions=[{"question_id":"q1","question":"Who is the counterparty?","reason":"Material event is incomplete.","priority":80,"confidence":.4,"related_evidence_id":5}])
    d=ExecutiveReasoningEngine().reason(context)[0]
    assert d.kind==DecisionKind.ACTION and d.related_question_ids==["q1"]

def test_high_confidence_learning_becomes_opportunity():
    context=BrainContext(learnings=[{"candidate_id":"l1","source_label":"A","target_label":"B","relation":"supplies","confidence":.9}])
    assert ExecutiveReasoningEngine().reason(context)[0].kind==DecisionKind.OPPORTUNITY

def test_brief_is_sorted_and_summarized():
    context=BrainContext(events=[{"event_id":"e1","object":{"label":"Failed item"},"transition":"failed","closure":"open","confidence":.9,"evidence_id":None},{"event_id":"e2","object":{"label":"Open request"},"transition":"requested","closure":"open","confidence":.7,"evidence_id":None}],confidence=.8,confidence_band="likely")
    brief=ExecutiveReasoningEngine().executive_brief(context)
    assert brief["summary"]["decision_count"]==2
    assert brief["summary"]["risk_count"]==1
    assert brief["decisions"][0]["priority"]>=brief["decisions"][1]["priority"]
