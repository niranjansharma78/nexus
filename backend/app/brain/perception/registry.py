from __future__ import annotations

from .sensor import NexusSensor


class SensorRegistry:
    def __init__(self) -> None:
        self._sensors: dict[str, NexusSensor] = {}

    def register(
        self,
        sensor: NexusSensor,
        *,
        replace: bool = False,
    ) -> NexusSensor:
        key = sensor.sensor_id.casefold()

        if key in self._sensors and not replace:
            raise ValueError(f"Sensor already registered: {sensor.sensor_id}")

        self._sensors[key] = sensor
        return sensor

    def get(self, sensor_id: str) -> NexusSensor | None:
        return self._sensors.get(sensor_id.casefold())

    def enabled(self) -> list[NexusSensor]:
        return [
            sensor
            for sensor in self._sensors.values()
            if sensor.enabled
        ]

    def list(self) -> list[dict[str, object]]:
        return [
            sensor.metadata()
            for sensor in sorted(
                self._sensors.values(),
                key=lambda item: item.sensor_id.casefold(),
            )
        ]
