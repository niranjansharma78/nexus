from __future__ import annotations
from app.brain.core.context import BrainContext
from app.brain.executive_reasoning.models import DecisionKind, UniversalDecision

class ExecutiveReasoningEngine:
    def reason(self, context: BrainContext) -> list[UniversalDecision]:
        decisions=[]
        for event in context.events:
            confidence=float(event.get("confidence",0.0)); closure=event.get("closure","open"); transition=event.get("transition")
            label=event.get("object",{}).get("label","Untitled event"); evidence_id=event.get("evidence_id")
            if closure=="open" and transition in {"failed","expired","escalated"}:
                decisions.append(UniversalDecision(title=f"Review risk: {label}",kind=DecisionKind.RISK,priority=self._score(importance=.9,urgency=.9,confidence=confidence),confidence=confidence,importance=.9,urgency=.9,why_now="This open event represents a failed, expired, or escalated state.",recommended_action="Review the cause and assign corrective action.",related_event_ids=[event["event_id"]],evidence_ids=[evidence_id] if evidence_id else [])); continue
            if closure=="open" and transition in {"requested","committed","approved","started","progressed","transferred"}:
                decisions.append(UniversalDecision(title=f"Monitor open commitment: {label}",kind=DecisionKind.ACTION,priority=self._score(importance=.7,urgency=.6,confidence=confidence),confidence=confidence,importance=.7,urgency=.6,why_now="This event remains open and has not reached a terminal outcome.",recommended_action="Confirm the next expected transition.",related_event_ids=[event["event_id"]],evidence_ids=[evidence_id] if evidence_id else []))
        for question in context.open_questions:
            confidence=float(question.get("confidence",0.0)); priority=float(question.get("priority",50))/100.0
            decisions.append(UniversalDecision(title=question.get("question","Resolve open question"),kind=DecisionKind.ACTION,priority=self._score(importance=priority,urgency=priority,confidence=max(confidence,.5)),confidence=confidence,importance=priority,urgency=priority,why_now=question.get("reason","Nexus requires clarification to improve understanding."),recommended_action="Provide or locate the missing information.",related_question_ids=[question["question_id"]],evidence_ids=[question["related_evidence_id"]] if question.get("related_evidence_id") else []))
        for learning in context.learnings:
            confidence=float(learning.get("confidence",0.0))
            if confidence>=.85:
                source=learning.get("source_label","Unknown source"); relation=learning.get("relation","relates to"); target=learning.get("target_label","Unknown target")
                decisions.append(UniversalDecision(title=f"Validated pattern: {source} {relation} {target}",kind=DecisionKind.OPPORTUNITY,priority=self._score(importance=.6,urgency=.35,confidence=confidence),confidence=confidence,importance=.6,urgency=.35,why_now="An approved learning has reached high confidence and may support planning or automation.",recommended_action="Review whether this pattern should influence future decisions.",related_learning_ids=[learning["candidate_id"]]))
        return sorted(decisions,key=lambda item:item.priority,reverse=True)

    def executive_brief(self, context: BrainContext, *, limit:int=10) -> dict[str, object]:
        decisions=self.reason(context)[:max(1,min(limit,50))]
        return {"summary":{"decision_count":len(decisions),"risk_count":sum(i.kind==DecisionKind.RISK for i in decisions),"action_count":sum(i.kind==DecisionKind.ACTION for i in decisions),"opportunity_count":sum(i.kind==DecisionKind.OPPORTUNITY for i in decisions),"brain_confidence":context.confidence,"brain_confidence_band":context.confidence_band},"decisions":[i.to_dict() for i in decisions]}

    @staticmethod
    def _score(*, importance:float, urgency:float, confidence:float) -> float:
        raw=importance*.45+urgency*.35+confidence*.20
        return round(max(0.0,min(raw,1.0)),10)
