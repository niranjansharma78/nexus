from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import GraphEdge, GraphNode, KnowledgeLayer


class InMemoryKnowledgeGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._outgoing: dict[str, set[str]] = defaultdict(set)
        self._incoming: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node: GraphNode) -> GraphNode:
        self._nodes[node.node_id] = node
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        if edge.source_id not in self._nodes:
            raise ValueError("Edge source node does not exist")
        if edge.target_id not in self._nodes:
            raise ValueError("Edge target node does not exist")

        self._edges[edge.edge_id] = edge
        self._outgoing[edge.source_id].add(edge.edge_id)
        self._incoming[edge.target_id].add(edge.edge_id)
        return edge

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        return self._edges.get(edge_id)

    def nodes(
        self,
        *,
        layer: KnowledgeLayer | None = None,
        kind: str | None = None,
    ) -> list[GraphNode]:
        result = list(self._nodes.values())
        if layer is not None:
            result = [node for node in result if node.layer == layer]
        if kind is not None:
            result = [node for node in result if node.kind == kind]
        return result

    def edges(
        self,
        *,
        layer: KnowledgeLayer | None = None,
        relation: str | None = None,
    ) -> list[GraphEdge]:
        result = list(self._edges.values())
        if layer is not None:
            result = [edge for edge in result if edge.layer == layer]
        if relation is not None:
            result = [edge for edge in result if edge.relation == relation]
        return result

    def neighbors(
        self,
        node_id: str,
        *,
        relation: str | None = None,
        direction: str = "outgoing",
    ) -> list[GraphNode]:
        if node_id not in self._nodes:
            return []

        if direction not in {"outgoing", "incoming", "both"}:
            raise ValueError("Direction must be outgoing, incoming or both")

        edge_ids: set[str] = set()
        if direction in {"outgoing", "both"}:
            edge_ids.update(self._outgoing.get(node_id, set()))
        if direction in {"incoming", "both"}:
            edge_ids.update(self._incoming.get(node_id, set()))

        neighbor_ids: set[str] = set()
        for edge_id in edge_ids:
            edge = self._edges[edge_id]
            if relation is not None and edge.relation != relation:
                continue
            neighbor_ids.add(
                edge.target_id if edge.source_id == node_id else edge.source_id
            )

        return [self._nodes[item] for item in sorted(neighbor_ids)]

    def stats(self) -> dict[str, object]:
        node_layers = {
            layer.value: len(self.nodes(layer=layer))
            for layer in KnowledgeLayer
        }
        edge_layers = {
            layer.value: len(self.edges(layer=layer))
            for layer in KnowledgeLayer
        }
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "nodes_by_layer": node_layers,
            "edges_by_layer": edge_layers,
        }
