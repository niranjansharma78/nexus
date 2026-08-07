from pathlib import Path

from app.brain.runtime_v2.models import RuntimeTrigger
from app.brain.runtime_v2.service import CognitiveRuntimeV2


def test_runtime_composes_orchestrator(tmp_path: Path):
    result = CognitiveRuntimeV2(tmp_path / "brain.db").run(
        trigger="manual",
        objective="Supplier decision",
        world="factory",
        decision_options=[
            {
                "option_id": "wait",
                "label": "Wait",
                "expected_value": 0.5,
                "expected_risk": 0.5,
                "confidence": 0.7,
            },
            {
                "option_id": "replace",
                "label": "Replace",
                "expected_value": 0.9,
                "expected_risk": 0.2,
                "confidence": 0.9,
            },
        ],
    )

    assert result.succeeded is True
    assert result.orchestration is not None
    assert result.orchestration["decision"]["recommended_option_id"] == "replace"


def test_runtime_never_executes_actions(tmp_path: Path):
    result = CognitiveRuntimeV2(tmp_path / "brain.db").run(
        trigger=RuntimeTrigger.MANUAL,
        objective="Pay supplier",
        world="finance",
        plan_tasks=[
            {
                "title": "Prepare payment",
                "task_id": "prepare",
            }
        ],
        auto_execute_requested=True,
    )

    assert result.policy["execution_allowed"] is False
    assert result.requires_human_approval is True


def test_runtime_event_trigger_builds_context_request(tmp_path: Path):
    result = CognitiveRuntimeV2(tmp_path / "brain.db").run_from_event(
        {
            "event_id": "evt-1",
            "world": "factory",
            "source": "mes",
            "object": {
                "label": "Machine stopped",
            },
        }
    )

    assert result.trigger == RuntimeTrigger.EVENT
    assert result.objective == "Machine stopped"
    assert result.completed_at is not None


def test_low_impact_runtime_without_plan_still_does_not_execute(tmp_path: Path):
    result = CognitiveRuntimeV2(tmp_path / "brain.db").run(
        trigger="manual",
        objective="Review note",
        world="notes",
    )

    assert result.policy["execution_allowed"] is False
