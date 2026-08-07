ENGINE_MANIFEST = {
    "engine": "attention",
    "version": "2.2.0-alpha1",
    "standalone": True,
    "inputs": [
        "importance",
        "urgency",
        "novelty",
        "relevance",
        "risk",
        "confidence",
    ],
    "outputs": [
        "attention_score",
        "priority",
        "should_escalate",
        "should_process_now",
    ],
    "optional_dependencies": [
        "salience",
        "context",
        "runtime",
        "triggers",
    ],
    "api": True,
}
