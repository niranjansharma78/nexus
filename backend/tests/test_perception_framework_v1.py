from pathlib import Path

from app.brain.perception.models import Observation
from app.brain.perception.normalizer import EvidenceNormalizer
from app.brain.perception.pipeline import PerceptionPipeline
from app.brain.perception.registry import SensorRegistry
from app.brain.perception.testing_sensor import StaticSensor


def make_observation():
    return Observation(
        sensor_id="test-sensor",
        source="test",
        observed_at="2026-08-06T10:00:00+00:00",
        raw_payload={
            "type": "message",
            "subject": "Customer request",
        },
        confidence=0.8,
    )


def test_normalizer_creates_stable_fingerprint():
    normalizer = EvidenceNormalizer()
    observation = make_observation()

    first = normalizer.normalize(observation)
    second = normalizer.normalize(observation)

    assert first.fingerprint == second.fingerprint
    assert first.evidence_type == "message"


def test_registry_rejects_duplicate_sensor():
    registry = SensorRegistry()
    sensor = StaticSensor("test", [])

    registry.register(sensor)

    try:
        registry.register(sensor)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_pipeline_creates_evidence(tmp_path: Path):
    database = tmp_path / "brain.db"
    registry = SensorRegistry()
    registry.register(
        StaticSensor(
            "test-sensor",
            [make_observation()],
        )
    )

    result = PerceptionPipeline(
        database,
        registry,
    ).run_once()

    assert result.sensors_checked == 1
    assert result.observations_seen == 1
    assert result.evidence_created == 1
    assert result.duplicates_skipped == 0
    assert result.succeeded is True


def test_pipeline_deduplicates_replayed_observation(tmp_path: Path):
    database = tmp_path / "brain.db"
    registry = SensorRegistry()
    registry.register(
        StaticSensor(
            "test-sensor",
            [make_observation()],
        )
    )
    pipeline = PerceptionPipeline(database, registry)

    first = pipeline.run_once()
    second = pipeline.run_once()

    assert first.evidence_created == 1
    assert second.evidence_created == 0
    assert second.duplicates_skipped == 1
