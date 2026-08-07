ENGINE_MANIFEST = {
    "engine": "decision",
    "version": "1.7.0-alpha1",
    "standalone": True,
    "inputs": [
        "objective",
        "options",
        "context",
        "predictions",
        "simulations",
        "constraints",
        "intent",
    ],
    "outputs": [
        "ranked_options",
        "recommended_option",
        "decision_record",
    ],
    "optional_dependencies": [
        "context",
        "prediction",
        "simulation",
        "memory",
        "reflection",
    ],
    "api": True,
}
