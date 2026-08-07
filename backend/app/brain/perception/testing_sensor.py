from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    Observation,
    SensorHealth,
    SensorHealthState,
)
from .sensor import NexusSensor


class StaticSensor(NexusSensor):
    def __init__(
        self,
        sensor_id: str,
        observations: list[Observation],
    ) -> None:
        self.sensor_id = sensor_id
        self.sensor_name = f"Static Sensor {sensor_id}"
        self.enabled = True
        self._observations = observations
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def poll(self) -> list[Observation]:
        if not self._connected:
            raise RuntimeError("Sensor is not connected")
        return list(self._observations)

    def health(self) -> SensorHealth:
        return SensorHealth(
            sensor_id=self.sensor_id,
            state=(
                SensorHealthState.HEALTHY
                if self._connected
                else SensorHealthState.OFFLINE
            ),
            last_success_at=(
                datetime.now(timezone.utc).isoformat()
                if self._connected
                else None
            ),
            records_processed=len(self._observations),
        )
