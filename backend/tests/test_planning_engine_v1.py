from pathlib import Path

import pytest

from app.brain.planning.models import PlanTask, PlanStatus, TaskStatus
from app.brain.planning.service import PlanningEngine


def test_plan_marks_root_task_ready():
    task = PlanTask(title="Start", task_id="a")
    plan = PlanningEngine().create_plan(
        objective="Test",
        tasks=[task],
    )

    assert plan.tasks[0].status == TaskStatus.READY
    assert plan.status == PlanStatus.ACTIVE


def test_dependency_blocks_until_parent_complete(tmp_path: Path):
    engine = PlanningEngine(tmp_path / "brain.db")

    first = PlanTask(title="First", task_id="a")
    second = PlanTask(
        title="Second",
        task_id="b",
        dependencies=["a"],
    )

    plan = engine.create_plan(
        objective="Test",
        tasks=[first, second],
    )

    assert next(t for t in plan.tasks if t.task_id == "b").status == TaskStatus.BLOCKED

    plan = engine.update_task(
        plan.plan_id,
        "a",
        status=TaskStatus.COMPLETED,
    )

    assert next(t for t in plan.tasks if t.task_id == "b").status == TaskStatus.READY


def test_circular_dependency_rejected():
    a = PlanTask(title="A", task_id="a", dependencies=["b"])
    b = PlanTask(title="B", task_id="b", dependencies=["a"])

    with pytest.raises(ValueError):
        PlanningEngine().create_plan(
            objective="Cycle",
            tasks=[a, b],
        )


def test_critical_path_uses_duration():
    a = PlanTask(title="A", task_id="a", duration_hours=2)
    b = PlanTask(
        title="B",
        task_id="b",
        duration_hours=4,
        dependencies=["a"],
    )
    c = PlanTask(title="C", task_id="c", duration_hours=3)

    plan = PlanningEngine().create_plan(
        objective="Critical path",
        tasks=[a, b, c],
    )

    assert plan.critical_path == ["a", "b"]


def test_completed_tasks_drive_plan_progress(tmp_path: Path):
    engine = PlanningEngine(tmp_path / "brain.db")
    plan = engine.create_plan(
        objective="Progress",
        tasks=[
            PlanTask(title="A", task_id="a"),
            PlanTask(title="B", task_id="b"),
        ],
    )

    updated = engine.update_task(
        plan.plan_id,
        "a",
        status=TaskStatus.COMPLETED,
    )

    assert updated.progress == 0.5


def test_repository_round_trip(tmp_path: Path):
    engine = PlanningEngine(tmp_path / "brain.db")

    created = engine.create_plan(
        objective="Supplier transition",
        tasks=[PlanTask(title="Qualify supplier", task_id="a")],
        world="factory",
        decision_refs=["decision-1"],
    )

    loaded = engine.repository.get(created.plan_id)

    assert loaded is not None
    assert loaded.objective == "Supplier transition"
    assert loaded.decision_refs == ["decision-1"]
