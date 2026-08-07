from __future__ import annotations


class RuntimePolicy:
    HIGH_IMPACT_WORLDS = {
        "finance",
        "health",
        "legal",
        "family",
        "employment",
        "safety",
    }

    def evaluate(
        self,
        *,
        world: str | None,
        has_plan: bool,
        auto_execute_requested: bool,
    ) -> dict[str, object]:
        high_impact = bool(world and world.casefold() in self.HIGH_IMPACT_WORLDS)
        approval_required = high_impact or has_plan or auto_execute_requested

        return {
            "world": world,
            "high_impact": high_impact,
            "has_plan": has_plan,
            "auto_execute_requested": auto_execute_requested,
            "approval_required": approval_required,
            "execution_allowed": False,
            "reason": (
                "Human approval required before consequential execution."
                if approval_required
                else "No execution is performed by Runtime v2."
            ),
        }
