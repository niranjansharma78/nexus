from __future__ import annotations

from app.brain.graph.models import GraphEdge, GraphNode, KnowledgeLayer
from app.brain.graph.store import InMemoryKnowledgeGraph
from app.brain.ontology.models import UniversalEvent


def map_event_to_graph(
    graph: InMemoryKnowledgeGraph,
    event: UniversalEvent,
) -> dict[str, str]:
    event_node = graph.add_node(
        GraphNode(
            kind="event",
            label=event.object.label,
            layer=KnowledgeLayer.REALITY,
            confidence=1.0,
            external_id=event.event_id,
            attributes={
                "transition": event.transition.value,
                "state": event.state,
                "source": event.source,
                "occurred_at": event.occurred_at,
                "evidence_id": event.evidence_id,
            },
        )
    )

    object_node = graph.add_node(
        GraphNode(
            kind=event.object.kind,
            label=event.object.label,
            layer=KnowledgeLayer.REALITY,
            confidence=event.confidence,
            external_id=event.object.external_id,
            attributes=dict(event.object.attributes),
        )
    )

    graph.add_edge(
        GraphEdge(
            source_id=event_node.node_id,
            target_id=object_node.node_id,
            relation="concerns",
            layer=KnowledgeLayer.REALITY,
            confidence=1.0,
            evidence_ids=(
                (event.evidence_id,)
                if event.evidence_id is not None
                else ()
            ),
        )
    )

    result = {
        "event_node_id": event_node.node_id,
        "object_node_id": object_node.node_id,
    }

    if event.actor is not None:
        actor_node = graph.add_node(
            GraphNode(
                kind=event.actor.kind,
                label=event.actor.label,
                layer=KnowledgeLayer.REALITY,
                confidence=event.confidence,
                external_id=event.actor.external_id,
                attributes=dict(event.actor.attributes),
            )
        )
        graph.add_edge(
            GraphEdge(
                source_id=actor_node.node_id,
                target_id=event_node.node_id,
                relation="initiated",
                layer=KnowledgeLayer.REALITY,
                confidence=event.confidence,
            )
        )
        result["actor_node_id"] = actor_node.node_id

    if event.counterparty is not None:
        counterparty_node = graph.add_node(
            GraphNode(
                kind=event.counterparty.kind,
                label=event.counterparty.label,
                layer=KnowledgeLayer.REALITY,
                confidence=event.confidence,
                external_id=event.counterparty.external_id,
                attributes=dict(event.counterparty.attributes),
            )
        )
        graph.add_edge(
            GraphEdge(
                source_id=event_node.node_id,
                target_id=counterparty_node.node_id,
                relation="affects",
                layer=KnowledgeLayer.REALITY,
                confidence=event.confidence,
            )
        )
        result["counterparty_node_id"] = counterparty_node.node_id

    return result
