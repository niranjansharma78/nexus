from pathlib import Path

from app.brain.orchestrator.models import OrchestrationRequest
from app.brain.orchestrator.service import CognitiveOrchestrator


def test_orchestrator_can_run_decision_and_plan(tmp_path: Path):
    request = OrchestrationRequest(
        objective="Supplier transition",
        world="factory",
        intent="reduce delivery risk",
        decision_options=[
            {
                "option_id": "wait",
                "label": "Wait",
                "expected_value": 0.5,
                "expected_risk": 0.5,
                "confidence": 0.8,
            },
            {
                "option_id": "replace",
                "label": "Replace",
                "expected_value": 0.9,
                "expected_risk": 0.2,
                "confidence": 0.9,
            },
        ],
        plan_tasks=[
            {
                "title": "Qualify supplier",
                "task_id": "qualify",
            }
        ],
    )

    result = CognitiveOrchestrator(
        tmp_path / "brain.db"
    ).run(request)

    assert result.decision is not None
    assert result.decision["recommended_option_id"] == "replace"
    assert result.plan is not None
    assert result.plan["decision_refs"]


def test_orchestrator_keeps_engines_optional(tmp_path: Path):
    request = OrchestrationRequest(
        objective="Context only",
        context_query="nothing",
    )

    result = CognitiveOrchestrator(
        tmp_path / "brain.db"
    ).run(request)

    assert result.completed_at is not None
    assert result.decision is None
    assert result.plan is None


def test_orchestrator_isolates_stage_failure(tmp_path: Path):
    request = OrchestrationRequest(
        objective="Broken simulation",
        simulation_options=[
            {
                "option_id": "a",
                "label": "A",
                "outcomes": [
                    {
                        "label": "Bad",
                        "probability": 2.0,
                        "value_score": 0.5,
                        "risk_score": 0.5,
                        "confidence": 0.5,
                    }
                ],
            }
        ],
        decision_options=[
            {
                "option_id": "safe",
                "label": "Safe",
                "expected_value": 0.5,
                "expected_risk": 0.2,
                "confidence": 0.8,
            }
        ],
    )

    result = CognitiveOrchestrator(
        tmp_path / "brain.db"
    ).run(request)

    assert any(
        item.startswith("simulation_failed:")
        for item in result.errors
    )
    assert result.decision is not None
