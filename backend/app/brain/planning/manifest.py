ENGINE_MANIFEST = {
    "engine": "planning",
    "version": "1.8.0-alpha1",
    "standalone": True,
    "inputs": [
        "objective",
        "tasks",
        "dependencies",
        "constraints",
        "decision_refs",
        "simulation_refs",
    ],
    "outputs": [
        "plan",
        "critical_path",
        "progress",
        "replanning_required",
    ],
    "optional_dependencies": [
        "decision",
        "simulation",
        "prediction",
        "context",
        "memory",
        "reflection",
    ],
    "api": True,
}
