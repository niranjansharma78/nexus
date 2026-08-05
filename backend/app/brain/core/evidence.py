from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EvidenceRef:
    evidence_id: int
    source: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.evidence_id < 1:
            raise ValueError("evidence_id must be positive")
        if not self.source.strip():
            raise ValueError("Evidence source is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Evidence confidence must be between 0 and 1")
