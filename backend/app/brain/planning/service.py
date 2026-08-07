from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import Plan, PlanStatus, PlanTask, TaskStatus
from .repository import PlanRepository


class PlanningEngine:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.repository = (
            PlanRepository(database_path)
            if database_path is not None
            else None
        )

    def create_plan(
        self,
        *,
        objective: str,
        tasks: list[PlanTask],
        world: str | None = None,
        decision_refs: list[str] | None = None,
        simulation_refs: list[str] | None = None,
        constraints: list[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Plan:
        self._validate_dependencies(tasks)

        plan = Plan(
            objective=objective,
            tasks=tasks,
            world=world,
            decision_refs=list(decision_refs or []),
            simulation_refs=list(simulation_refs or []),
            constraints=list(constraints or []),
            metadata=dict(metadata or {}),
        )
        plan.critical_path = self._critical_path(tasks)
        self._refresh(plan)

        if self.repository is not None:
            self.repository.save(plan)

        return plan

    def update_task(
        self,
        plan_id: str,
        task_id: str,
        *,
        status: TaskStatus | str | None = None,
        progress: float | None = None,
    ) -> Plan:
        if self.repository is None:
            raise RuntimeError("Repository required for persistent updates")

        plan = self.repository.get(plan_id)
        if plan is None:
            raise KeyError(f"Plan not found: {plan_id}")

        task = next((t for t in plan.tasks if t.task_id == task_id), None)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")

        if status is not None:
            task.status = TaskStatus(status)
        if progress is not None:
            if not 0.0 <= float(progress) <= 1.0:
                raise ValueError("progress must be between 0 and 1")
            task.progress = float(progress)

        if task.status == TaskStatus.COMPLETED:
            task.progress = 1.0
        elif task.progress >= 1.0:
            task.status = TaskStatus.COMPLETED

        self._refresh(plan)
        self.repository.save(plan)
        return plan

    def _refresh(self, plan: Plan) -> None:
        task_map = {task.task_id: task for task in plan.tasks}

        for task in plan.tasks:
            if task.status in {
                TaskStatus.COMPLETED,
                TaskStatus.CANCELLED,
                TaskStatus.IN_PROGRESS,
            }:
                continue

            dependencies = [
                task_map[dep_id]
                for dep_id in task.dependencies
                if dep_id in task_map
            ]

            if any(dep.status != TaskStatus.COMPLETED for dep in dependencies):
                task.status = TaskStatus.BLOCKED
            else:
                task.status = TaskStatus.READY

        plan.progress = round(
            sum(task.progress for task in plan.tasks) / len(plan.tasks),
            10,
        )

        blocked = [
            task for task in plan.tasks
            if task.status == TaskStatus.BLOCKED
        ]

        plan.replanning_required = bool(blocked) and not any(
            task.status in {TaskStatus.READY, TaskStatus.IN_PROGRESS}
            for task in plan.tasks
        )

        if all(
            task.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}
            for task in plan.tasks
        ):
            plan.status = PlanStatus.COMPLETED
        elif plan.replanning_required:
            plan.status = PlanStatus.BLOCKED
        else:
            plan.status = PlanStatus.ACTIVE

        plan.updated_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_dependencies(tasks: list[PlanTask]) -> None:
        ids = {task.task_id for task in tasks}
        if len(ids) != len(tasks):
            raise ValueError("Duplicate task_id detected")

        for task in tasks:
            missing = [dep for dep in task.dependencies if dep not in ids]
            if missing:
                raise ValueError(
                    f"Task {task.task_id} has missing dependencies: {missing}"
                )

        visiting: set[str] = set()
        visited: set[str] = set()
        task_map = {task.task_id: task for task in tasks}

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("Circular dependency detected")
            if task_id in visited:
                return

            visiting.add(task_id)
            for dep in task_map[task_id].dependencies:
                visit(dep)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in ids:
            visit(task_id)

    @staticmethod
    def _critical_path(tasks: list[PlanTask]) -> list[str]:
        task_map = {task.task_id: task for task in tasks}
        memo: dict[str, tuple[float, list[str]]] = {}

        def longest(task_id: str) -> tuple[float, list[str]]:
            if task_id in memo:
                return memo[task_id]

            task = task_map[task_id]
            if not task.dependencies:
                result = (task.duration_hours, [task_id])
            else:
                dependency_paths = [longest(dep) for dep in task.dependencies]
                best_duration, best_path = max(
                    dependency_paths,
                    key=lambda item: item[0],
                )
                result = (
                    best_duration + task.duration_hours,
                    best_path + [task_id],
                )

            memo[task_id] = result
            return result

        all_paths = [longest(task.task_id) for task in tasks]
        return max(all_paths, key=lambda item: item[0])[1]
