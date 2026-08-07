from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import SensorHealth
from .normalizer import EvidenceNormalizer
from .registry import SensorRegistry
from .repository import EvidenceRepository


@dataclass(slots=True)
class PerceptionCycleResult:
    sensors_checked: int = 0
    observations_seen: int = 0
    evidence_created: int = 0
    duplicates_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    health: list[SensorHealth] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return not self.errors


class PerceptionPipeline:
    def __init__(
        self,
        database_path: str | Path,
        registry: SensorRegistry,
    ) -> None:
        self.registry = registry
        self.normalizer = EvidenceNormalizer()
        self.repository = EvidenceRepository(database_path)

    def run_once(self) -> PerceptionCycleResult:
        result = PerceptionCycleResult()

        for sensor in self.registry.enabled():
            result.sensors_checked += 1

            try:
                sensor.connect()
                observations = sensor.poll()
                result.observations_seen += len(observations)

                for observation in observations:
                    evidence = self.normalizer.normalize(observation)

                    if self.repository.save_if_new(evidence):
                        result.evidence_created += 1
                    else:
                        result.duplicates_skipped += 1

                result.health.append(sensor.health())
            except Exception as exc:
                result.errors.append(
                    f"{sensor.sensor_id}: {exc}"
                )
                try:
                    result.health.append(sensor.health())
                except Exception:
                    pass
            finally:
                try:
                    sensor.shutdown()
                except Exception:
                    pass

        return result
