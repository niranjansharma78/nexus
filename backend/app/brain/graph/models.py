from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class KnowledgeLayer(StrEnum):
    REALITY = "reality"
    UNDERSTANDING = "understanding"
    WISDOM = "wisdom"


@dataclass(slots=True, frozen=True)
class GraphNode:
    kind: str
    label: str
    layer: KnowledgeLayer
    confidence: float
    node_id: str = field(default_factory=lambda: str(uuid4()))
    external_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("Node kind is required")
        if not self.label.strip():
            raise ValueError("Node label is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Node confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["layer"] = self.layer.value
        return data


@dataclass(slots=True, frozen=True)
class GraphEdge:
    source_id: str
    target_id: str
    relation: str
    layer: KnowledgeLayer
    confidence: float
    edge_id: str = field(default_factory=lambda: str(uuid4()))
    evidence_ids: tuple[int, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("Edge source is required")
        if not self.target_id.strip():
            raise ValueError("Edge target is required")
        if self.source_id == self.target_id:
            raise ValueError("Self-referencing edges are not allowed")
        if not self.relation.strip():
            raise ValueError("Edge relation is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("Edge confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["layer"] = self.layer.value
        data["evidence_ids"] = list(self.evidence_ids)
        return data
