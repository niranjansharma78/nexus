from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Observation, SensorHealth


class NexusSensor(ABC):
    sensor_id: str
    sensor_name: str
    enabled: bool = True

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def poll(self) -> list[Observation]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> SensorHealth:
        raise NotImplementedError

    def shutdown(self) -> None:
        return None

    def metadata(self) -> dict[str, object]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_name": self.sensor_name,
            "enabled": self.enabled,
        }
