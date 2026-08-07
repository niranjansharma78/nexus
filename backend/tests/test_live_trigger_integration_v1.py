from pathlib import Path

from app.brain.triggers.service import TriggerDispatcher


def test_event_trigger_runs_runtime(tmp_path: Path):
    dispatcher = TriggerDispatcher(tmp_path / "brain.db")

    result = dispatcher.submit(
        kind="event",
        payload={
            "event_id": "evt-1",
            "world": "factory",
            "source": "mes",
            "object": {"label": "Machine stopped"},
        },
        world="factory",
        source="mes",
    )

    assert result.accepted is True
    assert result.succeeded is True
    assert result.runtime_result is not None
    assert result.runtime_result["trigger"] == "event"


def test_duplicate_trigger_is_suppressed(tmp_path: Path):
    dispatcher = TriggerDispatcher(tmp_path / "brain.db")
    payload = {
        "event_id": "evt-dup",
        "world": "factory",
        "object": {"label": "Line stopped"},
    }

    first = dispatcher.submit(
        kind="event",
        payload=payload,
        world="factory",
        source="mes",
    )
    second = dispatcher.submit(
        kind="event",
        payload=payload,
        world="factory",
        source="mes",
    )

    assert first.accepted is True
    assert second.duplicate is True
    assert second.accepted is False


def test_deferred_trigger_can_be_processed_later(tmp_path: Path):
    dispatcher = TriggerDispatcher(tmp_path / "brain.db")

    queued = dispatcher.submit(
        kind="manual",
        payload={"objective": "Deferred review"},
        process_now=False,
    )

    assert queued.accepted is True
    assert queued.runtime_run_id is None

    results = dispatcher.process_pending()

    assert len(results) == 1
    assert results[0].succeeded is True


def test_evidence_trigger_maps_to_runtime(tmp_path: Path):
    dispatcher = TriggerDispatcher(tmp_path / "brain.db")

    result = dispatcher.submit(
        kind="evidence",
        payload={
            "title": "Supplier invoice received",
            "world": "finance",
        },
        world="finance",
        source="email",
    )

    assert result.succeeded is True
    assert result.runtime_result["trigger"] == "evidence"
