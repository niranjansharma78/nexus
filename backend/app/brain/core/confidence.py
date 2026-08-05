from __future__ import annotations


class ConfidenceService:
    @staticmethod
    def normalize(value: float) -> float:
        return round(max(0.0, min(float(value), 1.0)), 10)

    @staticmethod
    def combine(values: list[float]) -> float:
        if not values:
            return 0.0

        remaining_uncertainty = 1.0
        for value in values:
            normalized = ConfidenceService.normalize(value)
            remaining_uncertainty *= 1.0 - normalized

        return round(1.0 - remaining_uncertainty, 10)

    @staticmethod
    def average(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(
            sum(ConfidenceService.normalize(value) for value in values)
            / len(values),
            10,
        )

    @staticmethod
    def band(value: float) -> str:
        normalized = ConfidenceService.normalize(value)
        if normalized >= 0.85:
            return "high"
        if normalized >= 0.60:
            return "likely"
        return "review"
