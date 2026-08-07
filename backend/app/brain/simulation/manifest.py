ENGINE_MANIFEST = {
    "engine": "simulation",
    "version": "1.5.0-alpha1",
    "standalone": True,
    "inputs": ["current_state", "options", "constraints", "assumptions", "external_predictions"],
    "outputs": ["ranked_options", "expected_outcomes", "recommended_option"],
    "optional_dependencies": ["prediction", "context", "memory"],
    "api": True,
}
